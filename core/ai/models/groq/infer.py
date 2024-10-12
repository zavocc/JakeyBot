from core.exceptions import ChatHistoryFull
from os import environ
import litellm
import logging

class Completions:
    _model_provider_thread = "groq_models"

    def __init__(self, guild_id = None,
                 model_name = "llama-3.1-70b-versatile",
                 db_conn = None, **kwargs):
        
        if environ.get("GROQ_API_KEY"):
            logging.info("Using default GROQ API endpoint")
            self._model_name = "groq/" + model_name
        else:
            raise ValueError("No GROQ API key was set, this model isn't available")

        self._guild_id = guild_id
        self._history_management = db_conn

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")

        # System prompt
        if _chat_thread is None:
            _chat_thread = [{
                "role": "system",
                "content": system_instruction   
            }]

    
        
        # User prompt
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

        # Generate completion
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            api_key=environ.get("GROQ_API_KEY")
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(
            {
                "role": "assistant",
                "content": _answer
            }
        )

        return {"answer":_answer, "prompt_count":_prompt_count+1, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider_thread)