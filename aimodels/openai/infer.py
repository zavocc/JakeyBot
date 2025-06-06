from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
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
            raise ModelAPIKeyUnset("No OpenAI API key was set, this model isn't available")

        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

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
                "content": system_instruction   
            }]

        
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

        _chat_thread.append(_prompt)

        # Generate completion
        litellm.api_key = environ.get("OPENAI_API_KEY")
        if self._oai_endpoint:
            litellm.api_base = self._oai_endpoint
        if environ.get("LITELLM_DEBUG"):
            litellm._turn_on_debug() # Enable debugging
        
        # When O1 model is used, set reasoning effort to medium
        # Since higher can be costly and lower performs similarly to GPT-4o 
        _interstitial = None
        if "o1" in self._model_name or "o4-mini" in self._model_name:
            self._genai_params["reasoning_effort"] = "medium"
            self._genai_params["temperature"] = None

        _response = await litellm.acompletion(
            model=self._model_name,
            messages=_chat_thread,
            **self._genai_params
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        if _interstitial:
            await _interstitial.delete()

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _answer, self._discord_method_send)

        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
