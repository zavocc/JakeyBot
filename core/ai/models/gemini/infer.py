from core.exceptions import ChatHistoryFull
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from os import environ
from pathlib import Path
import aiofiles
import aiofiles.os
import aiohttp
import asyncio
import discord
import google.generativeai as genai
import google.api_core.exceptions
import importlib
import jsonpickle
import logging
import random

class GenAIConfigDefaults:
    def __init__(self):
        self.generation_config = {
            "temperature": 0.5,
            "top_p": 1,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        self.safety_settings_config = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]


class Completions(GenAIConfigDefaults):
    def __init__(self, client_session = None, guild_id = None, 
                 model = {"model_provider": "gemini", "model_name": "gemini-1.5-flash-002"}, 
                 db_conn = None, **kwargs):
        # This is needed since it gets the state from core.ai._runtime_client.AIClientSession
        if client_session is None:
            raise AttributeError("Client session has not been started")

        super().__init__()

        # Optional
        # To be set as
        # self.__discord_bot = bot
        if kwargs.get("_discord_bot") is not None and kwargs.get("_discord_ctx") is not None:
            self.__discord_bot: discord.Bot = kwargs.get("_discord_bot")
            self.__discord_ctx: discord.ApplicationContext = kwargs.get("_discord_ctx")

        self._Tool_use = None
        self.__discord_attachment_data = None
        self.__discord_attachment_uri = None

        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn
        
    async def _init_tool_setup(self):
        self._Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self.__discord_bot, self.__discord_ctx)

        if self._Tool_use.tool_name == "code_execution":
            self._Tool_use.tool_schema = "code_execution"

    async def input_file(self, attachment: discord.Attachment, **kwargs):
        # Download the attachment
        _xfilename = f"{environ.get('TEMP_DIR')}/JAKEY.{random.randint(518301839, 6582482111)}.{attachment.filename}"
        try:
            async with aiohttp.ClientSession() as _download_session:
                async with _download_session.get(attachment.url, allow_redirects=True) as _xattachments:
                    # write to file with random number ID
                    async with aiofiles.open(_xfilename, "wb") as filepath:
                        async for _chunk in _xattachments.content.iter_chunked(8192):
                            await filepath.write(_chunk)
        except aiohttp.ClientError as httperror:
            # Remove the file if it exists ensuring no data persists even on failure
            if Path(_xfilename).exists():
                await aiofiles.os.remove(_xfilename)
            # Raise exception
            raise httperror

        # Upload the file to the server
        try:
            _file_uri = await asyncio.to_thread(genai.upload_file, path=_xfilename, display_name=_xfilename.split("/")[-1])
            _msgstatus = None

            # Wait for the file to be uploaded
            while _file_uri.state.name == "PROCESSING":
                if kwargs.get("verbose_logs") is not None:
                    if _msgstatus is None:
                        _msgstatus = await self.__discord_ctx.send("⌛ Processing the file attachment... this may take a while")
                await asyncio.sleep(3)
                _file_uri = await asyncio.to_thread(genai.get_file, _file_uri.name)
        except Exception as e:
            await self.__discord_ctx.respond(f"❌ Sorry, I can't process the file attachment, please see console logs for more details")
            raise e
        finally:
            await aiofiles.os.remove(_xfilename)

        # Immediately use the "used" status message to indicate that the file API is used
        if kwargs.get("verbose_logs") == True:
            # Add caution that the attachment data would be lost in 48 hours
            await self.__discord_ctx.send("> 📝 **Note:** The submitted file attachment will be deleted from the context after 48 hours.")
        
        if _msgstatus is not None: await _msgstatus.delete()

        # Set the attachment variable
        self.__discord_attachment_uri = attachment.url
        self.__discord_attachment_data = _file_uri

    async def completion(self, prompt, system_instruction: str = None):
        _genai_client = genai.GenerativeModel(
            model_name=self._model_name,
            safety_settings=self.safety_settings_config,
            generation_config=self.generation_config,
            system_instruction=system_instruction,
        )

        answer = await _genai_client.generate_content_async({
                "role":"user",
                "parts":[
                    prompt
                ]
            })
        return answer.text

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model
        if self.__discord_bot is not None \
            and self.__discord_ctx is not None \
            and self._history_management is not None:
            await self._init_tool_setup()

        if self._Tool_use:
            tool_config = {'function_calling_config':self._Tool_use.tool_config}

            if hasattr(self._Tool_use, "file_uri") and self.__discord_attachment_uri is not None:
                self._Tool_use.file_uri = self.__discord_attachment_uri
            else:
                tool_config = {'function_calling_config':"NONE"}
        else:
            tool_config = None

        _genai_client = genai.GenerativeModel(
            model_name=self._model_name,
            safety_settings=self.safety_settings_config,
            generation_config=self.generation_config,
            system_instruction=system_instruction,
            tools=self._Tool_use.tool_schema if self._Tool_use else None
        )

        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")

        _chat_thread = await asyncio.to_thread(jsonpickle.decode, _chat_thread, keys=True) if _chat_thread is not None else []

        
        # Craft prompt
        final_prompt = [self.__discord_attachment_data, f'{prompt}'] if self.__discord_attachment_data is not None else f'{prompt}'
        chat_session = _genai_client.start_chat(history=_chat_thread if _chat_thread else None)

        # Re-write the history if an error has occured
        # For now this is the only workaround that I could find to re-write the history if there are dead file references causing PermissionDenied exception
        # when trying to access the deleted file uploaded using Files API. See:
        # https://discuss.ai.google.dev/t/what-is-the-best-way-to-persist-chat-history-into-file/3804/6?u=zavocc306
        try:
            answer = await chat_session.send_message_async(final_prompt, tool_config=tool_config)
        #  Retry the response if an error has occured
        except google.api_core.exceptions.PermissionDenied:
            _chat_thread = [
                {"role": x.role, "parts": [y.text]} 
                for x in chat_session.history 
                for y in x.parts 
                if x.role and y.text
            ]

            # Notify the user that the chat session has been re-initialized
            await self.__discord_ctx.send("> ⚠️ One or more file attachments or tools have been expired, the chat history has been reinitialized!")

            # Re-initialize the chat session
            chat_session = _genai_client.start_chat(history=_chat_thread)
            answer = await chat_session.send_message_async(final_prompt, tool_config=tool_config)

        # answer.parts is equivalent to answer.candidates[0].   content.parts[0] but it is a shorthand alias
        _candidates = answer.parts
        _func_call = None

        for _part in _candidates:
            if _part.code_execution_result:
                await self.__discord_ctx.send(f"Used: **{self._Tool_use.tool_human_name}**")
                continue

            if _part.function_call:
                _func_call = _part.function_call
                break

        if _func_call:
            # Call the function through their callables with getattr
            try:
                _result = await self._Tool_use._tool_function(**_func_call.args)
            except (AttributeError, TypeError) as e:
                await self.__discord_ctx.respond("⚠️ The chat thread has a feature is not available at the moment, please reset the chat or try again in few minutes")
                # Also print the error to the console
                logging.error("slashCommands>/ask: I think I found a problem related to function calling:", e)
                return

            # send it again, and lower safety settings since each message parts may not align with safety settings and can partially block outputs and execution
            answer = await chat_session.send_message_async(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(
                            function_response = genai.protos.FunctionResponse(
                                name = _func_call.name,
                                response = {"result": _result}
                            )
                        )
                    ]
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
                }
            )

            await self.__discord_ctx.send(f"Used: **{self._Tool_use.tool_human_name}**")

        return {"answer":answer.text, "prompt_count":_prompt_count+1, "chat_thread": chat_session.history}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        _encoded = await asyncio.to_thread(jsonpickle.encode, chat_thread, indent=4, keys=True)
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=_encoded, prompt_count=prompt_count, model_provider=self._model_provider)