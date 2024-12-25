import discord
import io
class Tool:
    tool_human_name = "Ideation Tools"
    tool_name = "ideation_tools"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "canvas",
                "description": "Ideate, brainstorm, and create draft content inside Discord thread to continue conversation with specified topic and content",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "thread_title": {
                            "type": "STRING"
                        },
                        "plan": {
                            "type": "STRING",
                        },
                        "content": {
                            "type": "STRING",
                        },
                        "code": {
                            "type": "STRING",
                        },
                        "todos": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            }
                        }
                    },
                    "required": ["thread_title", "plan", "content"]
                }
            },
            {
                "name": "artifacts",
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
        ]

    
    async def _tool_function_canvas(self, thread_title: str, plan: str, content: str, code: str = None, todos: list = None):
        # Check if we're in a server
        if not self.discord_ctx.guild:
            raise Exception("This tool can only be used in a server")

        # Create a new thread
        _msgstarter = await self.discord_ctx.channel.send(f"📃 Planning **{thread_title}**")
        _thread = await _msgstarter.create_thread(name=thread_title, auto_archive_duration=1440)

        # Send the plan
        # Encode and decode using bytes and later decode it again using string escape
        await _thread.send(f"**Plan:**\n{plan}")
        # Send the content
        await _thread.send(f"**Content:**\n{content}")
        # Send the code if available
        if code:
            await _thread.send(f"**Code:**\n```{code}```")
        # Send the todos if available
        if todos:
            await _thread.send(f"**Todos:**\n")
            for _todo in todos:
                await _thread.send(f"- {_todo}")

        return "Thread created successfully"

    async def _tool_function_artifacts(self, file_contents: str, file_name: str):
        # Send the file
        await self.method_send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"