from core.exceptions import ToolsUnavailable
from os import environ
from pathlib import Path
import aiofiles.os
import asyncio
import discord
import importlib
import jsonpickle
import logging
import litellm

class Completions:
    _model_provider_thread = "gemini_litellm"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.5-flash-002",
                 db_conn = None):
        super().__init__()

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn
        
    async def input_files(self, attachment: discord.Attachment, **kwargs):
        _attachment_prompt = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        self._file_data = _attachment_prompt


    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model and tools
        if hasattr(self, "_discord_method_send") and self._history_management is not None:
            try:
                _Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self._discord_method_send)
            except ModuleNotFoundError as e:
                logging.error("I cannot import the tool because the module is not found: %s", e)
                raise ToolsUnavailable

            #if _Tool_use.tool_name == "code_execution":
            #    _Tool_use.tool_schema = "code_execution"
        else:
            _Tool_use = None

        print(_Tool_use.tool_schema_json)

        # Load history
        _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": system_instruction   
            }]


        # Craft prompt
        _chat_thread.append(
             {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        )

        # Check if we have an attachment
        if self._file_data is not None:
            _chat_thread[-1]["content"].append(self._file_data)

        # Generate completion
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model="gemini/" + self._model_name,
            max_tokens=8192,
            temperature=0.7,
            api_key=environ.get("GEMINI_API_KEY"),
            tools=[_Tool_use.tool_schema_json]
        )

        print(_response)
        print(_response.choices[0].message.tool_calls[0].function.name  )

        return {"answer":answer.text, "chat_thread": chat_session.history}

    async def save_to_history(self, chat_thread = None):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=_encoded, model_provider=self._model_provider_thread)