from core.config import config
from discord.ext import commands
from discord import Member, DiscordException
import discord
import logging

class Misc(commands.Cog):
    """Use my other utilities here that can help make your server more active and entertaining"""
    def __init__(self, bot):
        self.bot = bot
        self.author = config.get("discord.bot_name", "Jakey Bot")

    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    async def mimic(self, ctx, user: Member, message_body: str):
        """Mimic as user!"""
        await ctx.response.defer(ephemeral=True)

        if isinstance(user, int):
            user = await self.bot.fetch_user(user)    
        avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        # Set display name depending on whether if the user joins in particular guild or in DMs to have different display names
        if ctx.guild:
            _xuser_display_name = await ctx.guild.fetch_member(user.id)
            user_name = f"{_xuser_display_name.display_name}"
        else:
            _xuser_display_name = await self.bot.fetch_user(user.id)
            user_name = f"{_xuser_display_name.display_name}"

        webhook = await ctx.channel.create_webhook(name=f"Mimic command by {self.author}")

        if not message_body:
            await ctx.respond("⚠️ Please specify a message to mimic!")
            return
        await webhook.send(content=message_body, username=user_name, avatar_url=avatar_url)
        await webhook.delete()
        
        await ctx.respond("✅ Done!")

    @mimic.error
    async def on_command_error(self, ctx: commands.Context, error: DiscordException):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadUnionArgument):
            await ctx.respond("⚠️ Please specify a valid discord user (or user id) and message to mimic!\n**Syntax:** `$mimic <user/user id> <message>`")
        elif isinstance(error, commands.CommandInvokeError) or isinstance(error, commands.MissingPermissions):
            await ctx.respond("❌ Sorry, webhooks are not enabled in this channel. Please enable webhooks in this channel to use this command.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs. Please use this command inside the guild.")
        elif isinstance(error, commands.ApplicationCommandInvokeError):
            await ctx.respond("⚠️ Please input a member")
        else:
            logging.error("An error has occurred while executing mimic command, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(Misc(bot))
