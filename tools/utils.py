from core.exceptions import CustomErrorMessage
from fastmcp import Client
from typing import Literal
import aiofiles
import aiofiles.os
import importlib
import logging
import yaml

# Utility function
async def fetch_actual_tool_name(tool_name: str) -> str:
    # Check if tool manifest exists
    if not aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml"):
        raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
    
    # Open the YAML
    async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
        _manifest = yaml.safe_load((await _manifest_file.read()))
        return _manifest["tool_name"]

class ToolUseInstance:
    def __init__(self):
        self.used_mcp = False

    # Fetch, parse, and validate tool schema
    async def fetch_and_load_tool_schema(self, tool_name: str, tool_type: Literal['openai', 'google']):
        if tool_name is None:
            return None

        _parsed_schemas = []
        
        # Check if tool manifest exists
        if not (await aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml")):
            raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
        
        # Open the YAML
        async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
            _manifest = yaml.safe_load((await _manifest_file.read()))
    
        # TODO: Chk if it's MCP
        # Iterate each list and pop one of the dict keys to validate
        if _manifest.get("is_mcp"):
            # NOTE: I don't think FastMCP supports non context managers
            # So instead we just keep the URL at a class level so we execute execute_mcp_tool without additional yaml loading step
            self.mcp_client = Client(_manifest.get("mcp_url"))

            async with self.mcp_client:
                # We craft parameters for MCP
                for _tools in (await self.mcp_client.list_tools()):
                    _constructed_tool_schema = {}

                    _constructed_tool_schema["name"] = _tools.name
                    _constructed_tool_schema["description"] = _tools.description
                    _constructed_tool_schema["parameters"] = _tools.inputSchema
                    
                    # Check if the format we're going to use is OpenAI or Google
                    if tool_type == 'openai':
                        _parsed_schemas.append(
                            {
                                "type": "function",
                                "function": _constructed_tool_schema
                            }
                        )
                    elif tool_type == 'google':
                        # We return the session for Google
                        return self.mcp_client.session
            
        else:
            # if the manifest is empty list, raise error
            if not _manifest.get("tool_list"):
                raise CustomErrorMessage("⚠️ The agent you selected is currently misconfigured, please choose another agent using `/agent` command")
    
            # Check if the format we're going to use is OpenAI or Google
            if tool_type == 'openai':
                for _schema in _manifest["tool_list"]:
                    _parsed_schemas.append(
                        {
                            "type": "function",
                            "function": _schema
                        }
                    )
            else:
                for _schema in _manifest["tool_list"]:
                    _parsed_schemas.append(_schema)

        return _parsed_schemas
    
    # For legacy tools that supports discord bot connection
    async def return_tool_object(self, tool_name: str, discord_context = None, discord_bot = None):
        if tool_name is None:
            return None

        try:
            _function_payload = importlib.import_module(f"tools.apis.{tool_name}.tool").Tools(
                method_send=discord_context.channel.send,
                discord_ctx=discord_context,
                discord_bot=discord_bot
            )
        except ModuleNotFoundError as e:
            logging.error("I cannot import the tool because the module is not found: %s", e)
            raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
        
        return _function_payload
    
    # Used in load_tools in models.providers.provider_name.utils
    async def mcp_check(self) -> bool:
        if hasattr(self, "used_mcp") and hasattr(self, "mcp_client"):
            return True
        return False

    # Remote MCP Execution
    # TODO: Add support for auth
    async def execute_mcp_tool(self, tool_name: str, arguments: dict) -> list:
        if not hasattr(self, "mcp_client"):
            return "Tool is not yet initialized, no action is performed."

        async with self.mcp_client:
            _outputs =  await self.mcp_client.call_tool(tool_name, arguments)
        return _outputs[0].text
    
    # Close client
    async def close_mcpclient(self):
        if hasattr(self, "mcp_client"):
            logging.info("Closing MCP Client session...")
            async with self.mcp_client:
                await self.mcp_client.close()
            logging.info("MCP Client session closed.")