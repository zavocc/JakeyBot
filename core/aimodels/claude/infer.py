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
        elif environ.get("OPENROUTER_API_KEY"):
            logging.info("Using OpenRouter API for Anthropic")

            # Normalize model names since the naming convention is different here
            if model_name == "claude-3-haiku-20240307":
                self._model_name = "openrouter/anthropic/" + "claude-3-haiku"
            elif model_name == "claude-3-5-sonnet-latest":
                self._model_name = "openrouter/anthropic/" + "claude-3.5-sonnet"
            elif model_name == "claude-3-5-sonnet-20240620":
                self._model_name = "openrouter/anthropic/" + "claude-3.5-sonnet-20240620"
            else:
                self._model_name = "openrouter/anthropic/" + model_name
            
            logging.info("Using normalized model name: %s", self._model_name)
        
        else:
            raise ValueError("No Anthropic API key was set, this model isn't available")
    
        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise MultiModalUnavailable

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
                        "cache_control": {
                            "type": "ephemeral"
                        }
                    }
                ]
            }
        )

        # Check if we have an attachment
        if self._file_data is not None:
            _chat_thread[-1]["content"].append(self._file_data)

        # Generate completion
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            api_key=environ.get("ANTHROPIC_API_KEY")
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
                        "text": _answer,
                        "cache_control": {
                            "type": "ephemeral"
                        }
                    }
                ]
            }
        )

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)