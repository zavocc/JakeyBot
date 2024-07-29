from core.ai.history import HistoryManagement as histmgmt
from discord.ext import commands
from os import environ
import discord

class ChatMgmt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

    ###############################################
    # Clear context command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    async def sweep(self, ctx):
        """Clear the context history of the conversation"""
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
        HistoryManagement = histmgmt(guild_id)
        _feature = await HistoryManagement.get_config()

        # Clear and set feature
        await HistoryManagement.clear_history()
        await HistoryManagement.set_config(_feature)

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
        choices=[
            discord.OptionChoice("Code Execution with Python", "code_execution"),
            discord.OptionChoice("Image Generator with Stable Diffusion 3", "image_generator"),
            discord.OptionChoice("Random Reddit", "randomreddit"),
            discord.OptionChoice("Web Browsing with DuckDuckGo", "web_browsing"),
            discord.OptionChoice("YouTube Search", "youtube")
        ]
    )
    async def feature(self, ctx, capability: str):
        """Enhance your chat with capabilities! Some are in BETA so things may not always pick up"""

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
        HistoryManagement = histmgmt(guild_id)

        # if tool use is the same, do not clear history
        #print(await HistoryManagement.get_config())
        _feature = await HistoryManagement.get_config()
        if _feature == capability:
            await ctx.respond("✅ Feature already enabled!")
        else:
            # clear and reinitialize history
            await HistoryManagement.clear_history()

            # set config
            await HistoryManagement.set_config(capability)
            await ctx.respond(f"✅ Feature **{capability}** enabled successfully and chat is reset to reflect the changes")
        
    # Handle errors
    @feature.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        await ctx.respond("❌ Something went wrong, please check the console logs for details.")
        raise error

def setup(bot):
    bot.add_cog(ChatMgmt(bot))
