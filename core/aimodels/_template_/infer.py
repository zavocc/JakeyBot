# type: ignore
from core.ai.core import Utils
import discord

# A base template for other models
class Completions():
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "agi-5-latest"):
        # Model provider thread
        self._model_provider_thread = "ai_provider_company"

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

        # Used for passing non-textual data into the model
        self._file_data = None # The attachment data itself (binary data, prompt, etc)

        # This is required - DO NOT MODIFY
        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn
        
    # A data must be assigned to the file_data attribute at the end
    async def input_files(self, attachment: discord.Attachment):
        pass

    # For non-chat completions
    async def completion(self, prompt, system_instruction: str = None) -> str:
       pass

    # For chat completions (required)
    # If the AI model doesn't properly support system_instruction, keep it as None or add handler
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None) -> dict:
        # Send the response
        await Utils.send_ai_response(self_discord.ctx, prompt, response, self._discord_method_send)
        return {"response":"OK", "chat_thread": []}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=_encoded, model_provider=self._model_provider_thread)