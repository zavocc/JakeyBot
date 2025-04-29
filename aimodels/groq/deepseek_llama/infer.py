from ..base import BaseInitProvider
from core.ai.core import Utils
from os import environ
import litellm
import re

class Completions(BaseInitProvider):
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "deepseek-r1-distill-llama-70b"):
        # Model provider thread
        self._model_provider_thread = "groq_deepseek"

        # Init
        super().__init__(discord_ctx, discord_bot, guild_id, model_name)
        
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
        litellm.api_key = environ.get("GROQ_API_KEY")
        if environ.get("LITELLM_DEBUG"):
            litellm._turn_on_debug()
        _params = {
            "messages": _chat_thread,
            "model": self._model_name,
            "max_tokens": 4096,
            "temperature": 0.7
        }
        _response = await litellm.acompletion(**_params)

        # Show the thought process inside the <think> tag
        _thoughts = re.findall(r"<think>(.*?)</think>", _response.choices[0].message.content, re.DOTALL)[0]
        # Show the thought process inside the <think> tag and format as quotes
        await Utils.send_ai_response(
            self._discord_ctx, 
            prompt, 
            "\n".join(f"> {line}" for line in _thoughts[:1924].strip().split("\n")),
            self._discord_method_send
        )

        # AI response (we clean the <think> tag and the response)
        _response.choices[0].message.content = re.sub(r"<think>(.*?)</think>", "", _response.choices[0].message.content, flags=re.DOTALL).strip()
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _answer, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)