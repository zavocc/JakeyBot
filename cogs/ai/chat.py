from core.ai.core import ModelsList
from cogs.ai.generative import BaseChat
from discord.ext import commands
from os import environ
import discord
import inspect

class Chat(BaseChat):
    def __init__(self, bot):
        super().__init__(bot)

    ###############################################
    # List models command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    async def models(self, ctx):
        """List all available models"""
        await ctx.response.defer(ephemeral=True)

        # Create an embed
        _embed = discord.Embed(
            title="Available models",
            description=inspect.cleandoc(
                """Here are the list of available models that you can use
                 
                To switch models, add this to your prompt /model:model-name to use a specific model when mentioning the bot
                Models are available and named as per the official model names

                Some models maybe aliased (e.g. -latest may be aliased to the last snapshot model) and some models may not be available"""),
            color=discord.Color.random()
        )

        # Iterate over models
        # Now we separate model provider into field and model names into value
        # It is __provider__model-name so we need to split it and group them as per provider
        _model_provider_tabledict = {}

        for _model in ModelsList.get_models_list(raw=True):
            _model_provider = _model.split("__")[1]
            _model_name = _model.split("__")[-1]

            # Add the model name to the corresponding provider in the dictionary
            if _model_provider not in _model_provider_tabledict:
                _model_provider_tabledict[_model_provider] = [_model_name]
            else:
                _model_provider_tabledict[_model_provider].append(_model_name)

        # Add fields to the embed
        for provider, models in _model_provider_tabledict.items():
            _embed.add_field(name=provider, value=", ".join(models), inline=False)

        # Send the status
        await ctx.respond(embed=_embed)

    ###############################################
    # Clear context command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    async def sweep(self, ctx):
        """Clear the context history of the conversation"""
        await ctx.response.defer()

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        else:
            guild_id = ctx.author.id

        # This command is available in DMs
        if ctx.guild is not None:
            # This returns None if the bot is not installed or authorized in guilds
            # https://docs.pycord.dev/en/stable/api/models.html#discord.AuthorizingIntegrationOwners
            if ctx.interaction.authorizing_integration_owners.guild == None:
                await ctx.respond("🚫 This commmand can only be used in DMs or authorized guilds!")
                return  

        # Initialize history
        _feature = await self.DBConn.get_config(guild_id=guild_id)

        # Clear and set feature
        await self.DBConn.clear_history(guild_id=guild_id)
        await self.DBConn.set_config(guild_id=guild_id, tool=_feature)

        await ctx.respond("✅ Chat history reset!")

    # Handle errors
    @sweep.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        # Get original error
        _error = getattr(error, "original")
        if isinstance(_error, PermissionError):
            await ctx.respond("⚠️ An error has occured while clearing chat history, logged the error to the owner")
        elif isinstance(_error, FileNotFoundError):
            await ctx.respond("ℹ️ Chat history is already cleared!")
        else:
            await ctx.respond("❌ Something went wrong, please check the console logs for details.")
            raise error

    ###############################################
    # Set chat features command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "capability",
        description = "Integrate tools to chat! Setting chat features will clear your history!",
        choices=ModelsList.get_tools_list(),
    )
    async def feature(self, ctx, capability: str):
        """Enhance your chat with capabilities! Some are in BETA so things may not always pick up"""
        # Defer
        await ctx.response.defer()

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        else:
            guild_id = ctx.author.id

        # This command is available in DMs
        if ctx.guild is not None:
            # This returns None if the bot is not installed or authorized in guilds
            # https://docs.pycord.dev/en/stable/api/models.html#discord.AuthorizingIntegrationOwners
            if ctx.interaction.authorizing_integration_owners.guild == None:
                await ctx.respond("🚫 This commmand can only be used in DMs or authorized guilds!")
                return

        # if tool use is the same, do not clear history
        _feature = await self.DBConn.get_config(guild_id=guild_id)
        if _feature == capability:
            await ctx.respond("✅ Feature already enabled!")
        else:
            # set config
            await self.DBConn.set_config(guild_id=guild_id, tool=capability)
            await ctx.respond(f"✅ Feature **{capability}** enabled successfully and chat is reset to reflect the changes")
        
    # Handle errors
    @feature.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        await ctx.respond("❌ Something went wrong, please check the console logs for details.")
        raise error

def setup(bot):
    bot.add_cog(Chat(bot))