from tools.builtin._base import BuiltInToolDiscordStateBase
import io
import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_file_write(self, file_contents: str, file_name: str):
        # Send the file
        await self.discord_message.channel.send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"
