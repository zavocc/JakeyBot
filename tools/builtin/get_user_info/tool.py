import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_message, discord_bot):
        self.discord_message: discord.Message = discord_message
        self.discord_bot: discord.Bot = discord_bot

    async def tool_get_user_info(self):
        _user: discord.User = self.discord_message.author
        return {
            "username": _user.name,
            "display_name": _user.display_name,
            "snowflake": _user.id,
            "created_at": _user.created_at.isoformat()
        }