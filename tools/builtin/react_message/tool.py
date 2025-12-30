import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx: discord.ApplicationContext = discord_ctx
        self.discord_bot: discord.Bot = discord_bot

    async def tool_react_message(self, emoji: str):
        try:
            await self.discord_ctx.add_reaction(emoji)
        except Exception:
            pass

        return "Reaction added successfully"