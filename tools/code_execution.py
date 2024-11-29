# Built in Tools
import google.generativeai as genai
import importlib

# Function implementations
class Tool:
    tool_human_name = "Code Execution with Python"
    tool_name = "code_execution"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {"code_execution": {}}
