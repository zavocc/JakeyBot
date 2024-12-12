from os import environ

class Tool:
    tool_human_name = "Canvas"
    tool_name = "canvas"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "functionDeclarations": [
                {
                    "name": self.tool_name,
                    "description": "Ideate, brainstorm, and create draft content inside Discord thread to continue conversation with specified topic and content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "thread_title": {
                                "type": "string"
                            },
                            "plan": {
                                "type": "string",
                            },
                            "content": {
                                "type": "string",
                            },
                            "code": {
                                "type": "string",
                            },
                            "todos": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["thread_title", "plan", "content"]
                    }
                }
            ]
        }

    
    async def _tool_function(self, thread_title: str, plan: str, content: str, code: str = None, todos: list = None):
        # Create a new thread
        _msgstarter = await self.discord_ctx.channel.send(f"📃 Planning **{thread_title}**")
        _thread = await _msgstarter.create_thread(name=thread_title, auto_archive_duration=1440)

        # Send the plan
        # Encode and decode using bytes and later decode it again using string escape
        await _thread.send(f"**Plan:**\n{bytes(plan, "utf-8").decode('unicode_escape')}")
        # Send the content
        await _thread.send(f"**Content:**\n{bytes(content, "utf-8").decode('unicode_escape')}")
        # Send the code if available
        if code:
            await _thread.send(f"**Code:**\n```{bytes(code, "utf-8").decode('unicode_escape')}```")
        # Send the todos if available
        if todos:
            await _thread.send(f"**Todos:**\n")
            for _todo in todos:
                await _thread.send(f"- {_todo}")

        return "Thread created successfully"