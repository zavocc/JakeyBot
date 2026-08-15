import discord

from jakeybot.agent.providers import GoogleAgent, OpenAIAgent


# Responsible for sending and receiving messages, handling tool loops, guards, loading and saving context
class AgentUserInstance:
    def __init__(self, userid: int, message: discord.Message, bot: discord.Bot):
        self.uid: int = userid
        self.message: discord.Message = message
        self.discord_bot: discord.Bot = bot

    def send_llm_message(self):
        openai_agent = OpenAIAgent()
        google_agent = GoogleAgent()
        print(openai_agent, google_agent)
