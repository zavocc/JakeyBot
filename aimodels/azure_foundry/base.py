from .config import ModelParams
from core.exceptions import ModelAPIKeyUnset
from os import environ
import discord

class BaseInitProvider:
    def __init__(self, discord_ctx: discord.ApplicationContext, discord_bot: discord.Bot, guild_id: int = None, model_name: str = None):
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
        self._guild_id = guild_id

        # Check for endpoints and keys
        # https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/how-to/create-model-deployments?pivots=ai-foundry-portal
        # Azure AI model inference must be used instead of serverless, managed compute, nor azure openai service
        # Check for keys
        if not environ.get("AZURE_AI_API_KEY"):
            raise ModelAPIKeyUnset("No AZURE_AI_API_KEY key was set, this model isn't available")

        if not environ.get("AZURE_AI_API_BASE"):
            raise ModelAPIKeyUnset("No AZURE_AI_API_BASE was set, this model isn't available. Please refer to https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/how-to/create-model-deployments?pivots=ai-foundry-portal")
       
        # Initiate model params
        self._model_params = ModelParams()