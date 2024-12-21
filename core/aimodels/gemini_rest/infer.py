from .helper_methods import hm_chunker, hm_raise_for_status
from .rest_params import RestParams
from core.exceptions import GeminiClientRequestError, SafetyFilterError, ToolsUnavailable
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

class Completions(RestParams):
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
        
        # Check if the AIOHTTP ClientSession for Gemini API is running
        if not hasattr(discord_bot, "_gemini_api_rest"):
            raise Exception("aiohttp client session for get and post requests in Gemini API not running, please check the bot configuration")
        
        # Check if _aiohttp_main_client_session is in the self._discord_bot object
        if not hasattr(discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        self._gemini_api_rest: aiohttp.ClientSession = discord_bot._gemini_api_rest
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
        async with self._gemini_api_rest.post(f"{self._api_endpoint_upload}",
                                        params={"key": environ.get("GEMINI_API_KEY")},
                                        headers=_initial_headers,
                                        json=_file_props) as _upload_response:
            await hm_raise_for_status(_upload_response)
                
            # Get the upload URL
            _upload_url = _upload_response.headers.get("X-Goog-Upload-URL")
           
        # Upload the actual bytes
        async with self._gemini_api_rest.post(_upload_url, headers=_upload_headers, data=hm_chunker(_xfilename)) as _upload_response:
            await hm_raise_for_status(_upload_response)
            
            # Get the file metadata
            _upload_info = (await _upload_response.json())["file"]

        # Check for status if there's still a processing step
        # We use a different endpoint to check the status of the file
        _msgstatus = None
        while "PROCESSING" in _upload_info["state"]:
            async with self._gemini_api_rest.get(f"{self._api_endpoint}/{_upload_info['name']}", 
                                                 params={'key': environ.get("GEMINI_API_KEY")}) as _upload_response:
                # Check if the request was successful
                await hm_raise_for_status(_upload_response)

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
    # Completion
    async def completion(self, prompt: typing.Union[str, list], system_instruction: str = None):
        # Check if the prompt is a string
        if isinstance(prompt, str):
            prompt = [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ],
                }
            ]
        elif isinstance(prompt, list):
            pass
        else:
            raise TypeError("Prompt must be either a string or a list")
        
        # Payload
        _payload = {
            "systemInstruction": {
                "role": "user",
                "parts": [
                    {
                        "text": system_instruction or "You are a helpful assistant"
                    }
                ]
            },
            "generationConfig": self._generation_config,
            "safetySettings": self._safety_settings,
            "contents": prompt,
        }

        # AIOHttp initial parameters
        _aiohttp_params = {
            "url": f"{self._api_endpoint}/models/{self._model_name}:generateContent",
            "params": {"key": environ.get("GEMINI_API_KEY")},
            "headers": {"Content-Type": "application/json"}
        }

        async with self._gemini_api_rest.post(**_aiohttp_params, json=_payload) as response:
            # Check for errors
            await hm_raise_for_status(response)
            
            # Get the response with starting first candidate
            _response = (await response.json())["candidates"][0]["content"]["parts"][-1]["text"]
            return _response

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
                        "text": system_instruction or "You are a helpful assistant"
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
                "tools":[_Tool.tool_schema],
                "toolConfig": {
                    "functionCallingConfig": {
                        "mode": "AUTO"
                    }
                },
            })

        # AIOHttp initial parameters
        _aiohttp_params = {
            "url": f"{self._api_endpoint}/models/{self._model_name}:generateContent",
            "params": {"key": environ.get("GEMINI_API_KEY")},
            "headers": {"Content-Type": "application/json"}
        }

        # POST request
        _retry = None
        async with self._gemini_api_rest.post(**_aiohttp_params, json=_payload) as response:
            # Check for errors
            if response.status == 403 and "do not have permission to access the File" in (await response.json())["error"]["message"]:
                await self._discord_method_send("⚠️ Something went wrong when making a request, cleaning the chat history and retrying...")
                # Add a status to retry
                _retry = True
            elif response.status >= 400:
                await hm_raise_for_status(response)
            else:
                # Get the response with starting first candidate
                _response = (await response.json())["candidates"][0]
            
        # We attempt to retry the requests by cleaning the chat h
        if _retry:
            # Format of the chat thread
            # _chat_thread = [
            #   {
            #     "parts": [
            #         {
            #             "fileData": {
            #                 "fileUri": "https://example.com/file.png",
            #                 "mimeType": "image/png"
            #              }
            #         }
            #     ],
            #     "role": "user"
            #   },
            #   {
            #     "parts": [
            #         {
            #             "text": "Summarize the image"
            #         }
            #     ],
            #     "role": "user"
            #   },
            # ]
            for _chat_turns in _chat_thread:
                for _chat_part in _chat_turns["parts"]:
                    if "fileData" in _chat_part:
                        _chat_part.clear()
                        _chat_part.update({
                            "text": "⚠️ The file attachment expired and was removed."
                        })
            
            # Retry the request
            async with self._gemini_api_rest.post(**_aiohttp_params, json=_payload) as response:
                # Raise an error if the request was not successful
                await hm_raise_for_status(response)

                _response = (await response.json())["candidates"][0]

        # Check if the response is empty or blocked by safety settings
        if _response["finishReason"] == "SAFETY":
            raise SafetyFilterError("The response was blocked by safety settings, rephrase the prompt or try again later")

        # Check if we need to execute Tools
        _tool_arg = None
        _tool_name = None
        for _partchk in _response["content"]["parts"]:
            if "functionCall" in _partchk:
                _tool_arg = _partchk["functionCall"]["args"]
                _tool_name = _partchk["functionCall"]["name"]
                break

            # Check if we have code execution response
            if "codeExecutionResult" in _partchk:
                await self._discord_method_send(f"✅ Used: **{_Tool.tool_human_name}**")
                break

        if _tool_arg and _tool_name:
            # Add previous interaction to the chat thread
            _chat_thread.append(_response["content"])

            # Indicate the tool is called
            await self._discord_method_send(f"✅ Used: **{_Tool.tool_human_name}**")

            # Call the tool
            try:
                if not hasattr(_Tool, "_tool_function"):
                    logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s", e)
                    raise ToolsUnavailable
    
                _toolResult = await _Tool._tool_function(**_tool_arg)
            # For other exceptions, log the error and add it as part of the chat thread
            except Exception as e:
                # Also print the error to the console
                logging.error("Something when calling specific tool lately, reason: %s", e)
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
                await hm_raise_for_status(response)

                _response = (await response.json())["candidates"][0]

            # Check if the response is empty or blocked by safety settings
            if _response["finishReason"] == "SAFETY":
                raise SafetyFilterError("The full response was blocked by safety settings, rephrase the prompt or try again later")

        _finalResponse = None
        # Find the text response since sometimes it triggers KeyError sometimes
        # If there are two text fields, append it to the final response
        for _part in _response["content"]["parts"]:
            if "text" in _part:
                if _finalResponse is not None:
                    _finalResponse += _part["text"]
                else:
                    _finalResponse = _part["text"]
                break
        
        # Custom Error
        if _finalResponse is None:
            raise GeminiClientRequestError(message="An error was occurred, the response was empty or not found", error_code=999)

        # Append to history
        _chat_thread.append(_response["content"])
        return {"answer": _finalResponse, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)