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
        self.mcp_client = None

    def _clean_schema_for_google(self, schema: dict) -> dict:
        if not isinstance(schema, dict):
            return schema
        
        _cleaned_schema = {}
        
        # Only keep allowed fields at any level
        _allowed_fields = {'type', 'enum', 'description', 'properties', 'items', 'required'}
        
        for k, v in schema.items():
            if k in _allowed_fields:
                if k == 'properties' and isinstance(v, dict):
                    # Recursively clean nested properties
                    _cleaned_schema[k] = {
                        prop_name: self._clean_schema_for_google(prop_value) 
                        for prop_name, prop_value in v.items()
                    }
                elif k == 'items' and isinstance(v, dict):
                    # Clean array items schema
                    _cleaned_schema[k] = self._clean_schema_for_google(v)
                else:
                    cleaned[key] = v
        
        return cleaned

    # Initialize MCP client
    async def init_fastmcp_client(self, mcp_url: str):
        if mcp_url:
            logging.info("Initializing MCP client with URL: %s", mcp_url)
            self.mcp_client = Client(mcp_url)
            self.used_mcp = True

    # Fetch, parse, and validate tool schema
    async def fetch_and_load_tool_schema(self, tool_name: str, tool_type: Literal['openai', 'google']) -> list:
        if tool_name is None:
            return None

        _parsed_schemas = []
        
        # Check if tool manifest exists
        if not (await aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml")):
            raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
        
        # Open the YAML
        async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
            _manifest = yaml.safe_load((await _manifest_file.read()))
    
        # Let's check if we have MCP initiated
        # Iterate each list and pop one of the dict keys to validate
        if self.mcp_client and self.used_mcp:
            async with self.mcp_client:
                # We craft parameters for MCP
                for _tools in (await self.mcp_client.list_tools()):
                    _constructed_tool_schema = {}

                    _constructed_tool_schema["name"] = _tools.name
                    _constructed_tool_schema["description"] = _tools.description
                    
                    
                    # Check if the format we're going to use is OpenAI or Google
                    if tool_type == 'openai':
                        _constructed_tool_schema["parameters"] = _tools.inputSchema
                        _parsed_schemas.append(
                            {
                                "type": "function",
                                "function": _constructed_tool_schema
                            }
                        )
                    elif tool_type == 'google':
                        _constructed_tool_schema["parameters"] = self._clean_schema_for_google(_tools.inputSchema)
                        # We return the session for Google
                        _parsed_schemas.append(_tools)
                        
        # Use legacy tools
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
    

    # Returns the MCP client URL for given tool name and None if not found
    async def determine_mcp_url(self, tool_name: str) -> str | None:
        if tool_name is None:
            return None

        # Check if tool manifest exists
        if not (await aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml")):
            raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
        
        # Open the YAML
        async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
            _manifest = yaml.safe_load((await _manifest_file.read()))
            if _manifest.get("is_mcp") and _manifest.get("mcp_url"):
                return _manifest["mcp_url"]
        
        return None

    # Used in load_tools in models.providers.provider_name.utils
    async def mcp_check(self) -> bool:
        if self.used_mcp and self.mcp_client:
            logging.info("MCP is enabled for this tool instance at this time.")
            return True
        return False

    # Remote MCP Execution
    # TODO: Add support for auth
    async def execute_mcp_tool(self, tool_name: str, arguments: dict) -> list:
        if not self.mcp_client and not self.used_mcp:
            return "Tool is not yet initialized, no action is performed."

        async with self.mcp_client:
            _outputs =  await self.mcp_client.call_tool(tool_name, arguments)
        return _outputs[0].text
    