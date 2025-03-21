from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from os import environ
import discord
import litellm

class Completions(ModelParams):
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "grok-beta"):
        super().__init__()

        # Discord context
        self._discord_ctx = discord_ctx

        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = self._discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = self._discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        # Check if discord_bot whether if its a subclass of discord.Bot
        if not isinstance(discord_bot, discord.Bot):
            raise Exception("Invalid discord bot object provided")
        
        # Discord bot object lifecycle instance
        self._discord_bot: discord.Bot = discord_bot

        if environ.get("XAI_API_KEY"):
            self._model_name = "xai/" + model_name
        else:
            raise ModelAPIKeyUnset("No XAI API key was set, this model isn't available")

        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment, extra_metadata: str = None):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

        self._file_data = {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": attachment.url
                    }
                },
                {
                    "type": "text",
                    "text": extra_metadata if extra_metadata else ""
                }
            ]
        }

    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        
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

        # Check for file attachments
        if hasattr(self, "_file_data"):
            _chat_thread.append(self._file_data)
        
        # Generate completion
        litellm.api_key = environ.get("XAI_API_KEY")
        litellm._turn_on_debug() # Enable debugging

        # Params and response
        _params = {
            "messages": _chat_thread,
            "model": self._model_name,
            "max_tokens": 4096,
            "temperature": 0.7
        }
        _response = await litellm.acompletion(**_params)

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message)

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _answer, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)