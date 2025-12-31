import discord
from tools.builtin._base import BuiltInToolDiscordStateBase

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_get_user_info(self):
        _user: discord.User = self.discord_message.author
        return {
            "username": _user.name,
            "display_name": _user.display_name,
            "snowflake": _user.id,
            "created_at": _user.created_at.isoformat()
        }
