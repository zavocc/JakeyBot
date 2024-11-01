from core.exceptions import ToolsUnavailable
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
    _model_provider_thread = "gemini"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.5-flash-002",
                 db_conn = None):
        super().__init__()

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn
        
    async def input_files(self, attachment: discord.Attachment, **kwargs):
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
        _msgstatus = None
        try:
            _file_uri = await asyncio.to_thread(genai.upload_file, path=_xfilename, display_name=_xfilename.split("/")[-1])

            # Wait for the file to be uploaded
            while _file_uri.state.name == "PROCESSING":
                if _msgstatus is None and hasattr(self, "_discord_method_send"):
                    _msgstatus = await self._discord_method_send("⌛ Processing the file attachment... this may take a while")
                await asyncio.sleep(3)
                _file_uri = await asyncio.to_thread(genai.get_file, _file_uri.name)
        except Exception as e:
            raise e
        finally:
            if _msgstatus: await _msgstatus.delete()
            await aiofiles.os.remove(_xfilename)

        # Set the attachment variable
        self._file_data = _file_uri

    async def completion(self, prompt, system_instruction: str = None):
        _genai_client = genai.GenerativeModel(
            model_name=self._model_name,
            safety_settings=self.safety_settings_config,
            generation_config=self.generation_config,
            system_instruction=system_instruction,
        )

        answer = await _genai_client.generate_content_async({
                "role":"user",
                "parts":prompt if isinstance(prompt, list) else [prompt]
            })
        return answer.text

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model and tools
        if hasattr(self, "_discord_method_send") and self._history_management is not None:
            try:
                _Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self._discord_method_send)
            except ModuleNotFoundError as e:
                logging.error("I cannot import the tool because the module is not found: %s", e)
                raise ToolsUnavailable

            if _Tool_use.tool_name == "code_execution":
                _Tool_use.tool_schema = "code_execution"
        else:
            _Tool_use = None

        _genai_client = genai.GenerativeModel(
            model_name=self._model_name,
            safety_settings=self.safety_settings_config,
            generation_config=self.generation_config,
            system_instruction=system_instruction,
            tools=_Tool_use.tool_schema if _Tool_use is not None else None
        )

        # Load history
        _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        _chat_thread = await asyncio.to_thread(jsonpickle.decode, _chat_thread, keys=True) if _chat_thread is not None else []

        # Craft prompt
        final_prompt = [self._file_data, f'{prompt}'] if self._file_data is not None else f'{prompt}'
        chat_session = _genai_client.start_chat(history=_chat_thread if _chat_thread else None)

        # Re-write the history if an error has occured
        # For now this is the only workaround that I could find to re-write the history if there are dead file references causing PermissionDenied exception
        # when trying to access the deleted file uploaded using Files API. See:
        # https://discuss.ai.google.dev/t/what-is-the-best-way-to-persist-chat-history-into-file/3804/6?u=zavocc306
        try:
            answer = await chat_session.send_message_async(final_prompt)
        #  Retry the response if an error has occured
        except google.api_core.exceptions.PermissionDenied:
            # Iterate over chat_session.history
            # Due to the uncanny use of protobuf objects but when iterating, each contains the format similar to this

            # {
            #    "role": "user",
            #    "parts": [
            #       "file_data": {
            #          "name": "file_name",
            #          "uri": "file_uri",
            #       },
            #       "text": "message"
            #    ]
            # }

            for _chat_parts in chat_session.history:
                # Remove the parts that contain "file_data"
                if _chat_parts.parts[0].file_data:
                    _chat_parts.parts.pop(0)

            # Notify the user that the chat session has been re-initialized
            await self._discord_method_send("> ⚠️ One or more file attachments or tools have been expired, the chat history has been reinitialized!")

            # Re-send the message
            answer = await chat_session.send_message_async(final_prompt)

        # answer.parts is equivalent to answer.candidates[0].   content.parts[0] but it is a shorthand alias
        _candidates = answer.parts
        _func_call = None

        for _part in _candidates:
            if _part.code_execution_result:
                self._used_tool_name = _Tool_use.tool_human_name
                continue

            if _part.function_call:
                _func_call = _part.function_call

                if _func_call:
                    # Call the function through their callables with getattr
                    try:
                        _result = await _Tool_use._tool_function(**_func_call.args)
                    except (AttributeError, TypeError) as e:
                        # Also print the error to the console
                        logging.error("ask command: I think I found a problem related to function calling:", e)
                        raise ToolsUnavailable
                    # For other exceptions, log the error and add it as part of the chat thread
                    except Exception as e:
                        # Also print the error to the console
                        logging.error("ask command: Something when calling specific tool lately, reason:", e)
                        _result = f"⚠️ Something went wrong while executing the tool: {e}, please tell the developer or the user to check console logs"
            
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

                    #await self._discord_method_send(f"Used: **{_Tool_use.tool_human_name}**")
                    self._used_tool_name = _Tool_use.tool_human_name

        return {"answer":answer.text, "chat_thread": chat_session.history}

    async def save_to_history(self, chat_thread = None):
        _encoded = await asyncio.to_thread(jsonpickle.encode, chat_thread, indent=4, keys=True)
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=_encoded, model_provider=self._model_provider_thread)