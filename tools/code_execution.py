# Built in Tools
import google.generativeai as genai
import importlib

# Function implementations
class Tool:
    tool_human_name = "Code Execution with Python"
    tool_name = "code_execution"
    tool_config = "AUTO"
    def __init__(self, bot, method_send):
        self.bot = bot
        self.method_send = method_send
