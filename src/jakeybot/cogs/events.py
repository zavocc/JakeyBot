import discord
from discord.ext import commands

from jakeybot import BotClient


class EventListeners(commands.Cog):
    def __init__(self, bot: BotClient): # pyright: ignore[reportMissingSuperCall]
        self.bot: BotClient = bot

    # on_message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        _ = await message.channel.send(f"{message.author.mention} said: {message.content}")

def setup(bot: BotClient):
    bot.add_cog(EventListeners(bot))
