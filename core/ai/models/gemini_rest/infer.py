import aiofiles.ospath
from core.exceptions import ToolsUnavailable
from os import environ
from pathlib import Path
import aiohttp
import aiofiles
import asyncio
import discord
import importlib
import logging
import random

class Completions():
    _model_provider_thread = "gemini_rest"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, 
                 model_name = "gemini-1.5-flash-002"):
        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        # Check if discord_bot whether if its a subclass of discord.Bot
        if not isinstance(discord_bot, discord.Bot):
            raise Exception("Invalid discord bot object provided")
        
        self._discord_bot = discord_bot
        
        # Check if the AIOHTTP ClientSession for Gemini API is running
        if not hasattr(discord_bot, "_gemini_api_rest"):
            raise Exception("AIOHttp Client Session for Gemini API (POST) not running, please check the bot configuration")
        
        # Check if _aiohttp_main_client_session is in the self._discord_bot object
        if not hasattr(discord_bot, "_aiohttp_main_client_session"):
            raise Exception("AIOHttp Client Session (MAIN/GET) not initialized, please check the bot configuration")
        
        self._gemini_api_rest: aiohttp.ClientSession = discord_bot._gemini_api_rest
        self._aiohttp_main_client_session: aiohttp.ClientSession = discord_bot._aiohttp_main_client_session

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id

        # REST parameters
        self._api_endpoint = "https://generativelanguage.googleapis.com/v1beta"
        self._api_endpoint_upload = "https://generativelanguage.googleapis.com/upload/v1beta/files"
        self._generation_config = {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }
        self._safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_LOW_AND_ABOVE"}
        ]

    ############################
    # File upload
    ############################
    async def _chunker(self, file_path, chunk_size=8192):
        async with aiofiles.open(file_path, "rb") as _file:
            _chunk = await _file.read(chunk_size)
            while _chunk:
                yield _chunk
                _chunk = await _file.read(chunk_size)

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

        # Upload the file to the server
        # Initial headers
        _initial_headers = {
            "Content-Type": "application/json",
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(attachment.size),
            "X-Goog-Upload-Header-Content-Type": attachment.content_type
        }
        _upload_headers = {
            "Content-Length": str(attachment.size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize"
        }
        _file_props = {
            "file": {
                "display_name": _xfilename.split("/")[-1]
            }
        }

        # Session for uploading the file
        async with self._gemini_api_rest.post(f"{self._api_endpoint_upload}?key={environ.get('GEMINI_API_KEY')}",
                                        headers=_initial_headers,
                                        json=_file_props) as _upload_response:
            _upload_url = _upload_response.headers.get("X-Goog-Upload-URL")

        # Upload the actual bytes
        async with self._gemini_api_rest.post(_upload_url, headers=_upload_headers, data=self._chunker(_xfilename)) as _upload_response:
            _upload_info = (await _upload_response.json())["file"]
            print(_upload_info)

        # Check for status if there's still a processing step
        # We use a different endpoint to check the status of the file
        _msgstatus = None
        while "PROCESSING" in _upload_info["state"]:
            async with self._gemini_api_rest.get(f"{self._api_endpoint}/{_upload_info['name']}", 
                                                 params={'key': environ.get("GEMINI_API_KEY")}) as _upload_response:
                _upload_info = await _upload_response.json()
                
                if _msgstatus is None:
                    _msgstatus = await self._discord_method_send(f"⌚ Processing the file attachment, this may take longer than usual...")
                
                # Prevent rate limiting from the Discord API
                await asyncio.sleep(2.5)
        else:
            if _msgstatus is not None:
                await _msgstatus.delete()

        # Cleanup
        if Path(_xfilename).exists():
            await aiofiles.os.remove(_xfilename)

        self._file_data = {"url":_upload_info["uri"], "mime_type":attachment.content_type}

    ############################
    # Inferencing
    ############################
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Tools
        try:
            _Tool = importlib.import_module(f"tools.{(await db_conn.get_config(guild_id=self._guild_id))}").Tool(
                method_send=self._discord_method_send,
                discord_bot=self._discord_bot
            )
        except ModuleNotFoundError as e:
            logging.error("%s: I cannot import the tool because the module is not found: %s", (await aiofiles.ospath.abspath(__file__)), e)
            raise ToolsUnavailable

        if _Tool.tool_name == "code_execution":
            _Tool.tool_schema_beta = {"code_execution": {}}

        print(_Tool.tool_schema_beta)

        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        print(_chat_thread)

        # Begin with the first user prompt
        if _chat_thread is None and not type(_chat_thread) == list:
            _chat_thread = []

        # Check if file attachment is present
        if self._file_data is not None:
            _chat_thread.append(
                {
                    "parts": [
                        {
                            "fileData": {
                                "fileUri": self._file_data["url"],
                                "mimeType": self._file_data["mime_type"]
                            }
                        }
                    ],
                    "role": "user"
                }
            )

        # User prompt
        _chat_thread.append(
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ],
                "role": "user",
            }
        )

        # Payload
        _payload = {
            "systemInstruction": {
                "role": "user",
                "parts": [
                    {
                        "text": system_instruction
                    }
                ]
            },
            "generationConfig": self._generation_config,
            "safetySettings": self._safety_settings,
            "contents": _chat_thread,
        }

        # Check if tool is available
        if _Tool is not None:
            _payload.update({
                "tools":[_Tool.tool_schema_beta],
                "toolConfig": {
                    "functionCallingConfig": {
                        "mode": "AUTO"
                    }
                },
            })

        # AIOHttp initial parameters
        _aiohttp_params = {
            "url": f"{self._api_endpoint}/models/{self._model_name}:generateContent?key={environ.get('GEMINI_API_KEY')}",
            "headers": {"Content-Type": "application/json"}
        }

        # POST request
        async with self._gemini_api_rest.post(**_aiohttp_params, json=_payload) as response:
            # Raise an error if the request was not successful
            try:
                response.raise_for_status()
            # Because this may print API keys, log the error and raise an exception
            except aiohttp.ClientResponseError as e:
                logging.error("%s: I think I found a problem related to the request: %s", (await aiofiles.ospath.abspath(__file__)), e)
                raise e

            await self._discord_method_send((await response.json()))

            # Get the response with starting first candidate
            _response = (await response.json())["candidates"][0]

        # Check if the response is empty or blocked by safety settings
        if _response["finishReason"] == "SAFETY":
            raise Exception("The response was blocked by safety settings, rephrase the prompt or try again later")

        # Check if we need to execute Tools
        _tool_arg = None
        _tool_name = None
        for x in _response["content"]["parts"]:
            await self._discord_method_send(x)
            if "functionCall" in x:
                _tool_arg = x["functionCall"]["args"]
                _tool_name = x["functionCall"]["name"]

        if _tool_arg and _tool_name:
            # Add previous interaction to the chat thread
            _chat_thread.append(_response["content"])

            # Call the tool
            try:
                _toolResult = await _Tool._tool_function(**_tool_arg)
            except (AttributeError, TypeError) as e:
                # Also print the error to the console
                logging.error("%s: I think I found a problem related to function calling: %s", (await aiofiles.ospath.abspath(__file__)), e)
                raise ToolsUnavailable
            # For other exceptions, log the error and add it as part of the chat thread
            except Exception as e:
                # Also print the error to the console
                logging.error("%s: Something when calling specific tool lately, reason: %s", (await aiofiles.ospath.abspath(__file__)), e)
                _toolResult = f"⚠️ Something went wrong while executing the tool: {e}, please tell the developer or the user to check console logs"

            # Add the result in chat thread and run inference
            _chat_thread.append({
                "parts": [
                    {
                        "functionResponse": {
                            "name": _tool_name,
                            "response": {
                                "result": _toolResult
                            }
                        }
                    }
                ],
                "role": "user"
            })
            _payload.update({"contents": _chat_thread})
            async with self._gemini_api_rest.post(**_aiohttp_params, json=_payload) as response:
                # Raise an error if the request was not successful
                response.raise_for_status()

                _response = (await response.json())["candidates"][0]

            # Check if the response is empty or blocked by safety settings
            if _response["finishReason"] == "SAFETY":
                raise Exception("The full response was blocked by safety settings, rephrase the prompt or try again later")

        # Append to history
        _chat_thread.append(_response["content"])
        return {"answer": _response["content"]["parts"][-1]["text"], "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)