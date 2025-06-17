from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from os import environ
import discord
import openai

class Completions(ModelParams):
    def __init__(self, model_name, discord_ctx, discord_bot, guild_id: int = None):
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

        # Check if _openai_client attribute is set
        if not hasattr(discord_bot, "_openai_client"):
            raise Exception("OpenAI client is not initialized, please check the bot initialization")
        
        # Check if OpenRouter API key is set
        if not environ.get("OPENAI_API_KEY"):
            raise ModelAPIKeyUnset("No OpenAI API key was set, this model isn't available")
        
        # Model name
        self._model_name = model_name

        self._guild_id = guild_id
        self._openai_client: openai.AsyncOpenAI = discord_bot._openai_client

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

        # Check if the model starts with o
        if self._model_name.startswith("o"):
            if not any(self._model_name.startswith(_oprefix) for _oprefix in ["o1-preview", "o1-mini"]):
                self._genai_params["reasoning_effort"] = "medium"

            # Always set temperature to 1 for reasoning models
            self._genai_params["temperature"] = 1

        _response = await self._openai_client.chat.completions.create(
            model=self._model_name,
            messages=_chat_thread,
            **self._genai_params
        )

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _response.choices[0].message.content, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
