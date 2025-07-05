from ..base import BaseInitProvider
from core.ai.core import Utils
from os import environ
import litellm
import re

class Completions(BaseInitProvider):
    def __init__(self, model_name, discord_ctx, discord_bot, guild_id: int = None):
        # Model provider thread
        self._model_provider_thread = "deepseek"

        # Init
        super().__init__(discord_ctx, discord_bot, guild_id, model_name)

        # Set the model
        self._model_name = "azure_ai/" + model_name
        
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

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
        litellm.api_key = environ.get("AZURE_AI_API_KEY")
        if environ.get("LITELLM_DEBUG"):
            litellm._turn_on_debug() # Enable debugging
        _response = await litellm.acompletion(model=self._model_name, messages=_chat_thread, **self._model_params.genai_params)

        # Show the thought process inside the <think> tag
        _custom_fields = _response.choices[0].message.provider_specific_fields
        _reasoning_content = _response.choices[0].message.reasoning_content
        if _custom_fields and _custom_fields.get("reasoning_content"):
            _thoughts = _custom_fields.get("reasoning_content")
        elif _reasoning_content:
            _thoughts = _reasoning_content
        else:
            _thoughts = None

        if _thoughts:
            # Show the thought process inside the <think> tag and format as quotes
            # There's always one <think>content</think> tag from the start of the response
            # so we assume it's the first one and we use [0] index
            # NOTE: Azure AI changed this behavior
            await Utils.send_ai_response(
                self._discord_ctx, prompt, 
                "\n".join(f"> {line}" for line in _thoughts[:1924].strip().split("\n")),
                self._discord_method_send
            )

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _response.choices[0].message.content, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)