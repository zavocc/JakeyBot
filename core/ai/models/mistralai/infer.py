from core.exceptions import ChatHistoryFull
from os import environ
import mistralai

class Completions:
    def __init__(self, guild_id = None, 
                 client_session = None,
                 model = {"model_provider": "mistralai", "model_name": "mistral-large-latest"}, 
                 db_conn = None, **kwargs):
        if client_session is None or not hasattr(client_session, "_mistral_client"):
            raise AttributeError("Mistral client session has not been set or initialized")

        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn

        if environ.get("MISTRAL_API_KEY") is None:
            raise Exception("Mistral API key is not configured. Please configure it and try again.")

        self.__mistral_client: mistralai.Mistral = client_session._mistral_client

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")

        # System prompt
        # Check if codestral-latest model is used since it's not necessary to put system instructions as its designed for code
        # And to prevent tokens from being depleted quickly
        if _chat_thread is None:
            if not self._model_name == "codestral-latest":
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
        _response = await self.__mistral_client.chat.complete_async(
            model=self._model_name,
            messages=_chat_thread
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
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider)