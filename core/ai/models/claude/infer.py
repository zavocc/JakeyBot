from core.exceptions import MultiModalUnavailable, ChatHistoryFull
from os import environ
import discord
import openai

class Completions:
    def __init__(self, client_session = None, guild_id = None, 
                 model = {"model_provider": "claude", "model_name": "claude-3-haiku"}, 
                 db_conn = None, **kwargs):
        if client_session is None or not hasattr(client_session, "_orouter"):
            raise AttributeError("OpenRouter (using OpenAI SDK) client session has not been set or initialized")

        self._file_data = None

        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn

        self.__orouter_client: openai.AsyncClient = client_session._orouter

    async def input_files(self, attachment: discord.Attachment, **kwargs):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise MultiModalUnavailable("Only images are supported for this model")

        prompt_w_attachment = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        self._file_data = prompt_w_attachment

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")
        
        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_instruction,
                        "cache_control": {
                            "type": "ephemeral"
                        }
                    }
                ] 
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
        _response = await self.__orouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com/zavocc/JakeyBot",
                "X-Title": environ.get("BOT_NAME", "JakeyBot")
            },
            messages=_chat_thread,
            model=f"anthropic/{self._model_name}",
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
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider)