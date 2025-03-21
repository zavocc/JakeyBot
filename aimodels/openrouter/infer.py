from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from core.ai.history import History as typehint_History
from os import environ
import discord
import litellm
import logging

class Completions(ModelParams):
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = None):
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

        if not environ.get("OPENROUTER_API_KEY"):
            raise ModelAPIKeyUnset("No OpenRouter API key was set, this model isn't available")

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

    async def chat_completion(self, prompt, db_conn: typehint_History, system_instruction: str = None):
        # Before we begin, get the OpenRouter model name and override self._model_name
        _model_name = await db_conn.get_key(guild_id=self._guild_id, key="default_openrouter_model")

        # If the key returns none, use gpt-4o-mini as default
        if _model_name is None:
            self._model_name = "openrouter/openai/gpt-4o-mini"
        else:
            self._model_name = "openrouter/" + _model_name

        # Indicate the model name
        logging.info("Using OpenRouter model: %s", self._model_name)

        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        # PaLM models don't have system prompt
        if _chat_thread is None:
            if not "palm" in self._model_name:
                # Begin with system prompt
                _chat_thread = [{
                    "role": "system",
                    "content": [{
                        "type": "text",
                        "text": system_instruction
                    }]
                }]

                # If it's from Anthropic, also append "cache_control" block to system prompt
                if "claude-3" in self._model_name:
                    _chat_thread[-1]["content"][0]["cache_control"] = {
                        "type": "ephemeral"
                    }
    
            else:
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

        # Check if we have an attachment
        if hasattr(self, "_file_data"):
            if any(model in self._model_name for model in self._MULTIMODAL_MODELS):
                _chat_thread.append(self._file_data)
            else:
                raise CustomErrorMessage(f"🚫 The model **{self._model_name}** doesn't support file attachments, choose another model")

        # Params
        litellm.api_key = environ.get("OPENROUTER_API_KEY")
        litellm._turn_on_debug() # Enable debugging

        _params = {
            "messages": _chat_thread,
            "model": self._model_name,
            **self._genai_params
        }

        # Generate completion
        _response = await litellm.acompletion(**_params)

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        # Send message what model used
        await self._discord_method_send(f"-# Using OpenRouter model: **{self._model_name}**")

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _answer, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)