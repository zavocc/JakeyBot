import discord
import io

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_message, discord_bot):
        self.discord_message: discord.Message = discord_message
        self.discord_bot: discord.Bot = discord_bot

    async def tool_file_write(self, file_contents: str, file_name: str):
        # Send the file
        await self.discord_message.channel.send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"
