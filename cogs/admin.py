import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    # Shutdown command
    @commands.command(aliases=['exit', 'stop', 'quit', 'shutdown'])
    @commands.is_owner()
    async def admin_shutdown(self, ctx):
        """Shuts down the bot"""
        await ctx.send("Shutting down...")
        await self.bot.close()

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            await ctx.respond("❌ Sorry, only the owner can use this command.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(f"❌ You are missing the required permissions to use this command. Needed permissions:\n```{error}```")
        else:
            raise error

def setup(bot):
    bot.add_cog(Admin(bot))
