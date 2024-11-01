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
            
            # Normalize model names since the naming convention is different here
            if model_name == "mistral-large-2407":
                self._model_name = "openrouter/mistralai/" + "mistral-large"
            elif model_name == "open-mixtral-8x7b":
                self._model_name = "openrouter/mistralai/" + "mixtral-8x7b-instruct"
            elif model_name == "codestral-latest":
                # Only codestral-mamba is available in Mistral OpenRouter API while this one is the larger code model
                raise ValueError("codestral-latest model is not available in Mistral OpenRouter API")
            else:
                self._model_name = "openrouter/mistralai/" + model_name

            logging.info(f"Using normalized model name: {self._model_name}")
        else:
            raise ValueError("No Mistral API key was set, this model isn't available")

        self._guild_id = guild_id
        self._history_management = db_conn

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        # System prompt
        # Check if codestral model is used since it's not necessary to put system instructions as its designed for code
        # And to prevent tokens from being depleted quickly
        if _chat_thread is None:
            if not "codestral" in self._model_name:
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

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)