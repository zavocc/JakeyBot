from core.exceptions import ChatHistoryFull
from os import environ
import litellm
import logging

class Completions:
    _model_provider_thread = "mistralai"

    def __init__(self, guild_id = None,
                 model_name = "mistral-large-2407",
                 db_conn = None):
        
        if environ.get("MISTRAL_API_KEY"):
            logging.info("Using default Mistral API endpoint")
            self._model_name = "mistral/" + model_name
        elif environ.get("OPENROUTER_API_KEY"):
            logging.info("Using OpenRouter API for Mistral")
            self._model_name = "openrouter/mistralai/" + model_name
        else:
            raise ValueError("No Mistral API key was set, this model isn't available")

        self._guild_id = guild_id
        self._history_management = db_conn

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")

        # System prompt
        # Check if codestral-latest model is used since it's not necessary to put system instructions as its designed for code
        # And to prevent tokens from being depleted quickly
        if _chat_thread is None:
            if not "codestral-latest" in self._model_name:
                _chat_thread = [{
                    "role": "system",
                    "content": system_instruction   
                }]
            else:
                _chat_thread = []
    
        
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
            api_key=environ.get("MISTRAL_API_KEY")
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