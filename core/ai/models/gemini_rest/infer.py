from os import environ
from pathlib import Path
import aiohttp
import aiofiles
import discord
import json
import random

class Completions():
    _model_provider_thread = "gemini_rest"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.5-flash-002",
                 db_conn = None):
        super().__init__()

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn

        # REST parameters
        self._api_endpoint = "https://generativelanguage.googleapis.com/v1beta"
        self._api_endpoint_upload = "https://generativelanguage.googleapis.com/upload/v1beta/files"
        self._headers = {"Content-Type": "application/json"}
        self._generation_config = {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }

    # Chunker for file uploads using aiofiles and this is a generator method
    async def _chunker(self, file_path, chunk_size=8192):
        async with aiofiles.open(file_path, "rb") as _file:
            while True:
                _chunk = _file.read(chunk_size)
                if not _chunk:
                    break
                yield _chunk


    async def input_files(self, attachment: discord.Attachment):
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
        
        # Upload the file to the GCS ephemeral bucket
        _initial_headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Headers-Content-Length": str(attachment.size),
            "X-Goog-Upload-Headers-Content-Type": attachment.content_type,
            "Content-Type": "application/json"
        }
        _upload_payload = {
            "file": {
                "display_name": _xfilename.split("/")[-1]
            }
        }

        # Upload the file
        _upload_status = None
        async with aiohttp.ClientSession() as _upload_session:
            # Initial resumable request so we can put the binary data later
            async with _upload_session.post(f"{self._api_endpoint_upload}?key={environ.get('GEMINI_API_KEY')}",
                                            headers=_initial_headers,
                                            json=_upload_payload) as _upload_response:
                # Raise an error if the request was not successful
                if _upload_response.status != 200:
                    raise Exception(f"Upload failed with status code {_upload_response.status}, with reason {_upload_response.reason}")
                
                # Get the upload status
                _upload_status = await _upload_response.content.read()
                print(_upload_status)
            
            async with _upload_session.post(f"{self._api_endpoint_upload}?key={environ.get('GEMINI_API_KEY')}",
                                            ) as _upload_response:
                # Raise an error if the request was not successful
                if _upload_response.status != 200:
                    raise Exception(f"Upload failed with status code {_upload_response.status}, with reason {_upload_response.reason}")

                _upload_status = await _upload_response.json()
                print(_upload_status)

        self._file_data = {"url":_upload_status["file"]["uri"], "mime_type":attachment.content_type}

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        print(_chat_thread)

        _Tool = {"code_execution": {}}

        # Begin with the first user prompt
        if _chat_thread is None and not type(_chat_thread) == list:
            _chat_thread = [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ],
                    "role": "user",
                }
            ]
        else:
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
            "contents": _chat_thread,
            "tools": [_Tool]
        }

        # POST request
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self._api_endpoint}/models/{self._model_name}:generateContent?key={environ.get('GEMINI_API_KEY')}",
                                    headers=self._headers,
                                    json=_payload) as response:
                # Raise an error if the request was not successful
                if response.status != 200:
                    raise Exception(f"Request failed with status code {response.status} with reason {response.reason}")

                _response = await response.json()
                await self._discord_method_send(_response)

        # Append to history
        _chat_thread.append(_response["candidates"][0]["content"])
        return {"answer": _response["candidates"][0]["content"]["parts"][-1]["text"], "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)