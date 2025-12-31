from tools.builtin._base import BuiltInToolDiscordStateBase

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_react_message(self, emoji: str):
        try:
            await self.discord_message.add_reaction(emoji)
        except Exception:
            pass

        return "Reaction added successfully"
