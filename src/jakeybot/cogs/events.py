import discord
from discord.ext import commands


class EventListeners(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    # on_message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        await message.channel.send(f"{message.author.mention} said: {message.content}")

def setup(bot: discord.Bot):
    bot.add_cog(EventListeners(bot))
