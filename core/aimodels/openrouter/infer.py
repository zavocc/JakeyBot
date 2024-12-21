from core.exceptions import MultiModalUnavailable
from core.ai.history import History
from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "openrouter"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = None):
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

        self._file_data = None

        if not environ.get("OPENROUTER_API_KEY"):
            raise ValueError("No OpenRouter API key was set, this model isn't available")

        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise MultiModalUnavailable("⚠️ This model only supports image attachments")

        _attachment_prompt = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        self._file_data = _attachment_prompt

    async def chat_completion(self, prompt, db_conn: History, system_instruction: str = None):
        # Before we begin, get the OpenRouter model name and override self._model_name
        _model_name = await db_conn.get_key(guild_id=self._guild_id, key="default_openrouter_model")

        # If the key returns none, use gpt-4o-mini as default
        if _model_name is None:
            self._model_name = "openrouter/gpt-4o-mini"
        else:
            self._model_name = "openrouter/" + _model_name

        # Indicate the model name
        logging.info("Using OpenRouter model: %s", self._model_name)

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

        # Check if we have an attachment
        # It is only supported with OpenAI, Anthropic, or XAI models for now
        if self._file_data is not None:
            if "openai" in self._model_name or "anthropic" in self._model_name or "gemini" in self._model_name or "grok" in self._model_name:
                _chat_thread[-1]["content"].append(self._file_data)
            else:
                await self._discord_method_send(f"⚠️ The model **{self._model_name}** doesn't support file attachments, thus will be ignored")

        # Params
        _params = {
            "messages": _chat_thread,
            "model": self._model_name,
            "max_tokens": 4096,
            "temperature": 0.7,
            "api_key": environ.get("OPENROUTER_API_KEY")
        }

        # Generate completion
        _response = await litellm.acompletion(
            **_params
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

        # Send message what model used
        await self._discord_method_send(f"-# Using OpenRouter model: **{self._model_name}**")

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)