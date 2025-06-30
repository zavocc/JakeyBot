# Built in Tools
from .manifest import ToolManifest
from os import environ
import aiohttp
import discord

# Function implementations
class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()

        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def _tool_function_web_search(self, **kwargs):
        pass
        

