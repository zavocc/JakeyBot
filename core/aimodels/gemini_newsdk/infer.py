from core.exceptions import ToolsUnavailable
from google import genai
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
    _model_provider_thread = "gemini_newsdk"

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
            _filedata = await self._gemini_api_client.aio.files.upload(path=_xfilename, config=types.UploadFileConfig(mime_type=attachment.content_type))

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

        self._file_data = {"file_uri": _filedata.uri, "mime_type": attachment.content_type}

    ############################
    # Inferencing
    ############################
    # Completion
    async def completion(self, prompt: typing.Union[str, list], system_instruction: str = None):
        pass

    # Chat Completion
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Tools
        try:
            _Tool = importlib.import_module(f"tools.{(await db_conn.get_config(guild_id=self._guild_id))}").Tool(
                method_send=self._discord_method_send,
                discord_ctx=self._discord_ctx,
                discord_bot=self._discord_bot
            )
        except ModuleNotFoundError as e:
            logging.error("I cannot import the tool because the module is not found: %s", e)
            raise ToolsUnavailable

        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        if _chat_thread is None:
            _chat_thread = []

        #print(_chat_thread)
        #print(len(_chat_thread))

        # Parse prompts
        _prompt = [
            types.Part.from_text(prompt),
        ]

        # File attachment
        if self._file_data is not None:
            _prompt.append(types.Part.from_uri(**self._file_data))

        # Add to chat thread so that the model can generate a response
        _chat_thread.append(types.Content(
            parts=_prompt,
            role="user"
        ).model_dump())

        # Check if tool is code execution
        if _Tool.tool_name == "code_execution":
            _tool_schema = types.Tool(code_execution=types.ToolCodeExecution())
        else:
            _tool_schema = types.Tool(function_declarations=[_Tool.tool_schema])

        # Create response
        _response = await self._gemini_api_client.aio.models.generate_content(
            model=self._model_name, 
            contents=_chat_thread,
            config=types.GenerateContentConfig(
                **self._genai_params,
                system_instruction=system_instruction or "You are a helpful assistant named Jakey",
                tools=[_tool_schema]
            )
        )

        # First candidate response
        _candidateContentResponse = _response.candidates[0].content

        # Tools
        _toolInvoke = None
        _codeExecutionResult = None
        _codeExecutionCode = None
        for _part in _candidateContentResponse.parts:
            if _part.function_call:
                _toolInvoke = _part.function_call
                break

            if _part.executable_code and not _codeExecutionCode:
                _codeExecutionCode = _part.executable_code

            if _part.code_execution_result and not _codeExecutionResult:
                _codeExecutionResult = _part.code_execution_result


        # Check if code execution was invoked
        # https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/code-execution
        if _codeExecutionCode and _codeExecutionResult:
            await self._discord_method_send(f"✅ Used: **{_Tool.tool_human_name}**")

            # Add the code execution result
            _chat_thread.append(types.Content(
                parts=[
                    types.Part.from_executable_code(
                        code=_codeExecutionCode.code,
                        language=_codeExecutionCode.language,
                    ),
                    types.Part.from_code_execution_result(
                        outcome=_codeExecutionResult.outcome,
                        output=_codeExecutionResult.output,
                    )
                ],
                role = "model"
            ).model_dump())

            _chat_thread.append(types.Content(
                parts=[
                    types.Part.from_text(
                        text="Explain the result of the code execution"
                    )
                ],
                role = "user"
            ).model_dump())
            
            # Re-run the model
            _response = await self._gemini_api_client.aio.models.generate_content(
                model=self._model_name, 
                config=types.GenerateContentConfig(
                    **self._genai_params,
                    system_instruction=system_instruction or "You are a helpful assistant named Jakey",
                ),
                contents=_chat_thread
            )

            _candidateContentResponse = _response.candidates[0].content
            
        # Check if we need to execute tools
        if _toolInvoke:
            # Ensure it has the context
            _chat_thread.append(_candidateContentResponse.model_dump())

            # Indicate the tool is called
            await self._discord_method_send(f"✅ Used: **{_Tool.tool_human_name}**")

            # Call the tool
            try:
                if not hasattr(_Tool, "_tool_function"):
                    logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s", e)
                    raise ToolsUnavailable
                _toolResult = {"toolResult": (await _Tool._tool_function(**_toolInvoke.args))}
            # For other exceptions, log the error and add it as part of the chat thread
            except Exception as e:
                # Also print the error to the console
                logging.error("Something when calling specific tool lately, reason: %s", e)
                _toolResult = {"error": f"⚠️ Something went wrong while executing the tool: {e}, please tell the developer or the user to check console logs"}

            # Return the tool result
            _chat_thread.append(types.Content(
                parts=[types.Part.from_function_response
                    (
                        name=_toolInvoke.name,
                        response=_toolResult
                    )
                ]).model_dump())
            
            # Re-run the model
            _response = await self._gemini_api_client.aio.models.generate_content(
                model=self._model_name, 
                config=types.GenerateContentConfig(
                    **self._genai_params,
                    system_instruction=system_instruction or "You are a helpful assistant named Jakey",
                ),
                contents=_chat_thread
            )

            _candidateContentResponse = _response.candidates[0].content

        # Append the response to the chat thread
        _chat_thread.append(_candidateContentResponse.model_dump())
        return {"answer": _response.text, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)