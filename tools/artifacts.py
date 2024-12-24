
import discord
import io
class Tool:
    tool_human_name = "Artifacts"
    tool_name = "artifacts"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "name": self.tool_name,
            "description": "Create convenient downloadable artifacts when writing code, markdown, text, or any other human readable content. When enabled, responses with code snippets and other things that demands file operations implicit or explictly will be saved as artifacts as Discord attachment.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "file_contents": {
                        "type": "STRING"
                    },
                    "file_name": {
                        "type": "STRING",
                    }
                },
                "required": ["file_contents", "file_name"]
            }
        }

    
    async def _tool_function(self, file_contents: str, file_name: str):
        # Send the file
        await self.method_send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"