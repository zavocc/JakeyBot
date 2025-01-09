from core.exceptions import CustomErrorMessage
from google import genai
from google.genai import errors
from google.genai import types
from os import environ
from pathlib import Path
import aiohttp
import aiofiles
import asyncio
import discord
import importlib
import logging
import typing
import random

class APIParams:
    def __init__(self):
        self._genai_params = {
            "candidate_count": 1,
            "max_output_tokens": 8192, 
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "safety_settings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }

class Completions(APIParams):
    _model_provider_thread = "gemini"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "gemini-1.5-flash-002"):
        super().__init__()

        # Discord context
        self._discord_ctx = discord_ctx

        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = self._discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = self._discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        # Check if discord_bot whether if its a subclass of discord.Bot
        if not isinstance(discord_bot, discord.Bot):
            raise Exception("Invalid discord bot object provided")
        
        # Discord bot object lifecycle instance
        self._discord_bot: discord.Bot = discord_bot
        
        # Check if _gemini_api_client is in the self._discord_bot object
        if not hasattr(discord_bot, "_gemini_api_client"):
            raise Exception("Gemini API client for completions not initialized, please check the bot configuration")

        # Check if _aiohttp_main_client_session is in the self._discord_bot object
        if not hasattr(discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        self._gemini_api_client: genai.Client = discord_bot._gemini_api_client
        self._aiohttp_main_client_session: aiohttp.ClientSession = discord_bot._aiohttp_main_client_session

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Download the attachment
        _xfilename = f"{environ.get('TEMP_DIR')}/JAKEY.{random.randint(518301839, 6582482111)}.{attachment.filename}"

        # Sometimes mimetype has text/plain; charset=utf-8, we need to grab the first part
        _mimetype = attachment.content_type.split(";")[0]
        try:
            async with self._aiohttp_main_client_session.get(attachment.url, allow_redirects=True) as _xattachments:
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
        
        # Upload the file
        _msgstatus = None
        try:
            _filedata = await self._gemini_api_client.aio.files.upload(path=_xfilename, config=types.UploadFileConfig(mime_type=_mimetype))

            while _filedata.state == "PROCESSING":
                if _msgstatus is None:
                    _msgstatus = await self._discord_method_send(f"⌚ Processing the file attachment, this may take longer than usual...")

                _filedata = await self._gemini_api_client.aio.files.get(name=_filedata.name)
                await asyncio.sleep(2.5)
        except Exception as e:
            raise e
        finally:
            if _msgstatus: await _msgstatus.delete()
            await aiofiles.os.remove(_xfilename)

        self._file_data = {"file_uri": _filedata.uri, "mime_type": _mimetype}

    ############################
    # Inferencing
    ############################
    # Completion
    async def completion(self, prompt: typing.Union[str, list], system_instruction: str = None):
        # Create response
        _response = await self._gemini_api_client.aio.models.generate_content(
            model=self._model_name, 
            contents=prompt,
            config=types.GenerateContentConfig(
                **self._genai_params,
                system_instruction=system_instruction or "You are a helpful assistant",
            )
        )

        return _response.text

    # Chat Completion
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Tools
        _tool_selection_name = await db_conn.get_config(guild_id=self._guild_id)
        try:
            if _tool_selection_name is None:
                _Tool = None
            else:
                _Tool = importlib.import_module(f"tools.{_tool_selection_name}").Tool(
                    method_send=self._discord_method_send,
                    discord_ctx=self._discord_ctx,
                    discord_bot=self._discord_bot
                )
        except ModuleNotFoundError as e:
            logging.error("I cannot import the tool because the module is not found: %s", e)
            raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")

        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        if _chat_thread is None:
            _chat_thread = []

        # Parse prompts
        _prompt = [
            types.Part.from_text(prompt),
        ]

        # File attachment
        if self._file_data is not None:
            _prompt.append(types.Part.from_uri(**self._file_data))

        # Disable tools entirely if the model has "gemini-2.0-flash-thinking-exp-1219"
        if self._model_name == "gemini-2.0-flash-thinking-exp-1219":
            _Tool = None

        # Check if tool is code execution
        if _Tool:
            if _tool_selection_name == "code_execution":
                _tool_schema = [types.Tool(code_execution=types.ToolCodeExecution())]
            else:
                # Check if the tool schema is a list or not
                # Since a list of tools could be a collection of tools, sometimes it's just a single tool
                # But depends on the tool implementation
                if type(_Tool.tool_schema) == list:
                    _tool_schema = [types.Tool(function_declarations=_Tool.tool_schema)]
                else:
                    _tool_schema = [types.Tool(function_declarations=[_Tool.tool_schema])]
        else:
            _tool_schema = None

        # Create chat session
        _chat_session = self._gemini_api_client.aio.chats.create(
            model=self._model_name,
            history=_chat_thread,
            config=types.GenerateContentConfig(
                **self._genai_params,
                system_instruction=system_instruction or "You are a helpful assistant named Jakey",
                tools=_tool_schema
            )
        )

        try:
            # First try
            _response = await _chat_session.send_message(_prompt)
        # Check if we get ClientError and has PERMISSION_DENIED
        except errors.ClientError as e:
            logging.error("1st try: I think I found a problem related to the request... doing first fixes: %s", e.message)
            if "do not have permission" in e.message:
                # Curated history attribute are list of multipart chat turns under Content structured datatype
                # Inside, it has "part" -> List and "role" -> str fields, so we iterate on the parts
                for _chat_turns in _chat_session._curated_history:
                    for _part in _chat_turns["parts"]:
                        # Check if we have file_data key then we just set it as None and set the text to "Expired"
                        if _part.get("file_data"):
                            _part["file_data"] = None
                            _part["text"] = "⚠️ The file attachment expired and was removed."
                
                # Notify the user that the chat session has been re-initialized
                await self._discord_method_send("> ⚠️ One or more file attachments or tools have been expired, the chat history has been reinitialized!")

                # Retry the request
                _response = await _chat_session.send_message(_prompt)
            else:
                logging.error("2nd try: I think I found a problem related to the request: %s", e.message)
                raise e

        # Check if the response was blocked due to safety and other reasons than STOP
        # https://ai.google.dev/api/generate-content#FinishReason
        if _response.candidates[0].finish_reason != "STOP":
            raise CustomErrorMessage("🤬 I detected unsafe content in your prompt, reason: `{}`. Please rephrase your question_response.candidates[0].finish_reason".format(_response.candidates[0].finish_reason))

        # Send the CoT process of the model if "gemin-2.0-flash-thinking-exp-1219" is used
        # Here we assume the CoT is always at the first index of the parts
        if self._model_name == "gemini-2.0-flash-thinking-exp-1219":
            await self._discord_method_send(f"> ℹ️ Below is Gemini's 2.0 thinking process and can produce undesirable outputs. Keep in mind that this model doesn't support tools, has 32k context, and only supports image and text inputs.")
            await self._discord_method_send(f"> {_response.candidates[0].content.parts[0].text.replace('\n', '\n> ')[:1950]}")

            # And discard the first part of the response since when switching Gemini models, it will intentionally produce a CoT
            # And save tokens, so we remove the first index
            _response.candidates[0].content.parts.pop(0)

        # Iterate through the parts and perform tasks
        _toolInvoke = []
        for _part in _response.candidates[0].content.parts:
            if _part.function_call:
                # Before we save it, unicode escape the function call arguments
                # This is because the generated arguments will provide literal escape characters, we need to parse it
                for _key, _value in _part.function_call.args.items():
                    if isinstance(_value, str):
                        # First try to fix common encoding issues
                        # This handles cases like Ã¢ÂÂ -> '
                        _value = _value.encode('utf-8').decode('utf-8')
                        _value = _value.encode().decode('unicode_escape')
                        _part.function_call.args[_key] = _value
                    # If the argument is a list, we need to iterate through it and fix string encoding issues in the list
                    elif isinstance(_value, list):
                        # Iterate through the list _list_value is the value of the list and _index is the index of the list
                        # We use enumerate to get the index of the list value each
                        for _index, _list_value in enumerate(_value):
                            if isinstance(_list_value, str):
                                # Also for this fix common encoding issues
                                _list_value = _list_value.encode('utf-8').decode('utf-8')
                                _list_value = _list_value.encode().decode('unicode_escape')
                                _part.function_call.args[_key][_index] = _list_value

                # Append the function call to the toolInvoke list
                _toolInvoke.append(_part.function_call)

            # Function calling and code execution doesn't mix
            if _part.executable_code:
                await self._discord_method_send(f"✅ Used: **{_Tool.tool_human_name}**")
                await self._discord_method_send(f"```py\n{_part.executable_code.code[:1975]}\n```")

            if _part.code_execution_result:
                # Send the code execution result
                await self._discord_method_send(f"```{_part.code_execution_result.output[:1975]}```")
            
        # Check if we need to execute tools
        if _toolInvoke:
            # Indicate the tool is called
            _interstitial = await self._discord_method_send(f"✅ Tool started: **{_Tool.tool_human_name}**")

            # Send text
            _firstTextResponseChunk = _response.candidates[0].content.parts[0].text
            if _firstTextResponseChunk and len(_firstTextResponseChunk) <= 2000:
                await self._discord_method_send(_firstTextResponseChunk)

            # If it has more than one function call arguments, we need to iterate through it
            # This is the case for Gemini 2.0, which otherwise it will error that it doesn't match the function call parts
            _toolParts = []

            # Indicator if there are errors
            _toHalt = False
            for _invokes in _toolInvoke:
                try:
                    # Edit the interstitial message
                    await _interstitial.edit(f"⚙️ Executing tool: **{_invokes.name}**")

                    if hasattr(_Tool, "_tool_function"):
                        _toExec = getattr(_Tool, "_tool_function")
                    elif hasattr(_Tool, f"_tool_function_{_invokes.name}"):
                        _toExec = getattr(_Tool, f"_tool_function_{_invokes.name}")
                    else:
                        logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s", e)
                        raise CustomErrorMessage("⚠️ An error has occurred while calling tools, please try again later or choose another tool")
            
                    # Check if _toHalts is True, if it is, we just need to tell the model to try again later
                    # Since its not possible to just break the loop, it has to match the number of parts of toolInvoke
                    if _toHalt:
                        _toolResult = {
                            "error": f"⚠️ Error occurred previously which in order to prevent further issues, the operation was halted",
                            "tool_args": _invokes.args
                        }
                    else:
                        _toolResult = {
                            "toolResult": (await _toExec(**_invokes.args)),
                            "tool_args": _invokes.args
                        }
                # For other exceptions, log the error and add it as part of the chat thread
                except Exception as e:
                    _toHalt = True

                    # Also print the error to the console
                    logging.error("Something when calling specific tool lately, reason: %s", e)
                    _toolResult = {
                        "error": f"⚠️ Something went wrong while executing the tool: {e}, please tell the developer or the user to check console logs and operation was halted",
                        "tool_args": _invokes.args
                    }

                _toolParts.append(types.Part.from_function_response(
                    name=_invokes.name,
                    response=_toolResult
                ))

            # Re-run the model
            await _interstitial.edit(f"✅ Generating a response with tool result from: **{_Tool.tool_human_name}**")
            _response = await _chat_session.send_message(_toolParts)

            # Edit interstitial message
            if _toHalt:
                await _interstitial.edit(f"⚠️ Error executing tool: **{_Tool.tool_human_name}**")
            else:
                await _interstitial.edit(f"✅ Used: **{_Tool.tool_human_name}**")

        # Save the latest messages to chat thread, if it's not a dict, it's a pydantic model object which we need to convert to dict
        _chat_thread = [_item if isinstance(_item, dict) else _item.model_dump(exclude_unset=True) for _item in _chat_session._curated_history]

        # Return the response
        _final_candidate_response = _response.candidates[0].content.parts
        return {"answer": _final_candidate_response[-1].text, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
