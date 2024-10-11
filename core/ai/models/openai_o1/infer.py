from core.exceptions import ChatHistoryFull
from os import environ
import openai

# OpenAI O1 model
class Completions:
    _model_provider_thread = "openai_o1"

    def __init__(self, guild_id = None, 
                 model_name = "o1-mini",
                 db_conn = None, **kwargs):
        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn

    async def chat_completion(self, prompt, **kwargs):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")

        if _chat_thread is None:
            _chat_thread = []

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

        # Generate completion
        _response = await self.__oaiclient.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com/zavocc/JakeyBot",
                "X-Title": environ.get("BOT_NAME", "JakeyBot")
            },
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            response_format={
                "type":"text"
            }
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

        return {"answer":_answer, "prompt_count":_prompt_count+1, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider_thread)