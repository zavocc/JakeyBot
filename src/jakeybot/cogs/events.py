import discord
from discord.ext import commands

from jakeybot import BotClient
from jakeybot.agent.message import AgentUserInstance


class EventListeners(commands.Cog):
    def __init__(self, bot):
        self.bot: BotClient = bot

    # on_message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        agenticSession = AgentUserInstance(message.author.id, message, self.bot)


        await message.channel.send(await agenticSession.send_llm_message())

def setup(bot: discord.Bot):
    bot.add_cog(EventListeners(bot))
