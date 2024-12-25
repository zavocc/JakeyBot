from core.exceptions import MultiModalUnavailable
from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "openai"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "gpt-4o-mini"):
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

        if environ.get("OPENAI_API_KEY"):
            # Set endpoint if OPENAI_API_ENDPOINT is set
            if environ.get("OPENAI_API_ENDPOINT"):
                self._oai_endpoint = environ.get("OPENAI_API_ENDPOINT")
                logging.info("Using OpenAI API endpoint: %s", self._oai_endpoint)
            else:
                self._oai_endpoint = None
                logging.info("Using default OpenAI API endpoint")
            self._model_name = "openai/" + model_name
        else:
            raise ValueError("No OpenAI API key was set, this model isn't available")

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
        if self._file_data is not None:
            _chat_thread[-1]["content"].append(self._file_data)

        # Params
        _params = {
            "messages": _chat_thread,
            "model": self._model_name,
            "max_tokens": 4096,
            "temperature": 0.7,
            "base_url": self._oai_endpoint,
            "api_key": environ.get("OPENAI_API_KEY")
        }

        # When O1 model is used, set reasoning effort to medium
        # Since higher can be costly and lower performs similarly to GPT-4o 
        _interstitial = None
        if "o1" in self._model_name:
            _interstitial = await self._discord_method_send("🔍 Used O1 model, please wait while I'm thinking...")
            _params["reasoning_effort"] = "medium"

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

        if _interstitial:
            await _interstitial.delete()

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
