from core.exceptions import MultiModalUnavailable
from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "genini_oai"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.0-pro",
                 db_conn = None):
        self._file_data = None

        if environ.get("GEMINI_API_KEY"):
            self._model_name = model_name
        else:
            raise ValueError("No Gemini API key was set, this model isn't available")

        self._guild_id = guild_id
        self._history_management = db_conn

    async def chat_completion(self, prompt, system_instruction: str = None):
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
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=environ.get("GEMINI_API_KEY")
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": _answer
                    }
                ]
            }
        )

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)