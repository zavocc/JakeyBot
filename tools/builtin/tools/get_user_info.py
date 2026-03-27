from tools.builtin._base import BuiltInToolDiscordStateBase
import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_get_user_info(self):
        _user: discord.User = self.discord_message.author
        return {
            "username": _user.name,
            "display_name": _user.display_name,
            # we stringify the snowflake to avoid issues passing the tool result which may cause integer overflow
            "snowflake": str(_user.id),
            "created_at": _user.created_at.isoformat(),
        }
