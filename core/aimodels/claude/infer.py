from core.exceptions import MultiModalUnavailable
from os import environ
import discord
import logging
import litellm

class Completions:
    _model_provider_thread = "claude"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "claude-3-5-haiku-20241022"):
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

        if environ.get("ANTHROPIC_API_KEY"):
            logging.info("Using default Anthropic API endpoint")
            self._model_name = "anthropic/" + model_name
        else:
            raise ValueError("No Anthropic API key was set, this model isn't available")
    
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

    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        # Count prompt tokens
        _tok_prompt = litellm.token_counter(text=prompt)

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
                        "text": prompt,
                    }
                ]
            }
        )

        if _tok_prompt >= 1024:
            await self._discord_method_send(f"-# This prompt has been cached to save costs")
            _chat_thread[-1]["content"][0]["cache_control"] = {
                "type": "ephemeral"
            }

        # Check if we have an attachment
        if self._file_data is not None:
            _chat_thread[-1]["content"].append(self._file_data)

        # Generate completion
        litellm.api_key = environ.get("ANTHROPIC_API_KEY")
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=4096,
            temperature=0.7
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

        # Cache the assistant response if it exceeds 1024 tokens
        if litellm.token_counter(text=_answer) >= 1024:
            await self._discord_method_send(f"-# The response has been cached to save costs")
            _chat_thread[-1]["content"][0]["cache_control"] = {
                "type": "ephemeral"
            }

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)