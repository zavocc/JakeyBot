import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_message, discord_bot):
        self.discord_message: discord.Message = discord_message
        self.discord_bot: discord.Bot = discord_bot

    async def tool_react_message(self, emoji: str):
        try:
            await self.discord_message.add_reaction(emoji)
        except Exception:
            pass

        return "Reaction added successfully"
