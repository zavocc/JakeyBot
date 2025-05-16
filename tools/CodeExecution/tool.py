from google.genai import types

class Tool:
    tool_human_name = "Code Execution with Python"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [types.Tool(code_execution=types.ToolCodeExecution)]