# Built in Tools
import google.generativeai as genai
import importlib

# Function implementations
class Tool:
    tool_human_name = "Code Execution with Python"
    tool_name = "code_execution"
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
