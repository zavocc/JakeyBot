import discord

from jakeybot import BotClient
from jakeybot.agent.providers import GoogleAgent, OpenAIAgent


# Responsible for sending and receiving messages, handling tool loops, guards, loading and saving context
class AgentUserInstance:
    def __init__(self, userid: int, message: discord.Message, bot: BotClient):
        self.uid = userid
        self.message = message
        self.discord_bot = bot

    async def send_llm_message(self):
        openai_agent = OpenAIAgent()
        google_agent = GoogleAgent(self.discord_bot.csession_google)
        print(openai_agent, google_agent)

        text = await google_agent.generate(self.message.content)
        return text
