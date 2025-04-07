from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from os import environ
import discord
import litellm
import re

class Completions(ModelParams):
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "claude-3-5-haiku-20241022"):
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

        if environ.get("ANTHROPIC_API_KEY"):
            self._model_name = "anthropic/" + model_name
        else:
            raise ModelAPIKeyUnset("No Anthropic API key was set, this model isn't available")
    
        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image or PDF
        if not "image" in attachment.content_type and not "pdf" in attachment.content_type:
            raise CustomErrorMessage("⚠️ This model only supports image or PDF attachments")

        if attachment.content_type.startswith("application/pdf"):
            self._file_data = [
                {
                    "type": "document",
                    "source": {
                        "type": "url",
                        "url": attachment.url
                    }
                }
            ]
        else:
            self._file_data = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": attachment.url
                    }
                }
            ]

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

        # If '/cache:true' is in the prompt, we need to cache the prompt
        # Search must be either have whitespace or start/end of the string
        if re.search(r"(^|\s)/cache:true(\s|$)", prompt):
            await self._discord_method_send("ℹ️ Caching the prompt to improve performance later.")
            # Remove the '/cache:true' from the prompt
            prompt = re.sub(r"(^|\s)/cache:true(\s|$)", "", prompt)

            _cachePrompt = True
        else:
            _cachePrompt = False

        # Craft prompt
        _prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ]
        }

        # Check if we have an attachment
        if hasattr(self, "_file_data"):
            # Add the attachment part to the prompt
            _prompt["content"].extend(self._file_data)

        
        if _cachePrompt:
            # Add cache control to the message
            _prompt["content"][-1]["cache_control"] = {
                "type": "ephemeral"
            }

        _chat_thread.append(_prompt)

        # Generate completion
        litellm.api_key = environ.get("ANTHROPIC_API_KEY")
        litellm._turn_on_debug() # Enable debugging
        
        _response = await litellm.acompletion(
            model=self._model_name,
            messages=_chat_thread,
            **self._genai_params
        )

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())
        
        # Answer
        _answer = _response.choices[0].message.content

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _answer, self._discord_method_send)

        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)