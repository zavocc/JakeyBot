import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_message, discord_bot):
        self.discord_message: discord.Message = discord_message
        self.discord_bot: discord.Bot = discord_bot

    async def tool_send_user_dm_message(self, message_content: str):
        # If it's more than 2000 characters, we need to split it up
        if len(message_content) > 2000:
            _chunks = [message_content[i:i+2000] for i in range(0, len(message_content), 2000)]
            for _chunk in _chunks:
                await self.discord_message.author.send(content=_chunk)
        else:
            await self.discord_message.author.send(content=message_content)
        return "DM message sent successfully"