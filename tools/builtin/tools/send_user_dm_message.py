from tools.builtin._base import BuiltInToolDiscordStateBase

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_send_user_dm_message(self, message_content: str):
        # If it's more than 2000 characters, we need to split it up
        if len(message_content) > 2000:
            _chunks = [message_content[i:i+2000] for i in range(0, len(message_content), 2000)]
            for _chunk in _chunks:
                await self.discord_message.author.send(content=_chunk)
        else:
            await self.discord_message.author.send(content=message_content)
        return "DM message sent successfully"
