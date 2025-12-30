import discord
import io

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx: discord.ApplicationContext = discord_ctx
        self.discord_bot: discord.Bot = discord_bot

    async def tool_file_write(self, file_contents: str, file_name: str):
        # Send the file
        await self.discord_ctx.channel.send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"