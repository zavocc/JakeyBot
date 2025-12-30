from core.exceptions import CustomErrorMessage
from typing import Literal
import aiofiles
import aiofiles.os
import importlib
import logging
import yaml

# Fetch, parse, and validate tool schema
async def fetch_tool_schema(tool_api_name: str, tool_type: Literal['openai', 'google']) -> list:
    if tool_api_name is None:
        return None

    _parsed_schemas = []
    
    # Check if tool manifest exists
    if not (await aiofiles.os.path.exists(f"tools/apis/{tool_api_name}/manifest.yaml")):
        raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")

    # Open the YAML
    async with aiofiles.open(f"tools/apis/{tool_api_name}/manifest.yaml") as _manifest_file:
        _manifest_list = yaml.safe_load((await _manifest_file.read()))

    # if the manifest is empty list, raise error
    if not _manifest_list.get("tool_list"):
        raise CustomErrorMessage("⚠️ The agent you selected is currently misconfigured, please choose another agent using `/agent` command")
    
    # Also add built-in tools from tools/builtin if there's both tool.py and manifest.yaml
    if await aiofiles.os.path.exists(f"tools/builtin") and await aiofiles.os.path.exists(f"tools/builtin/manifest.yaml"):
        async with aiofiles.open(f"tools/builtin/manifest.yaml") as _builtin_manifest_file:
            _builtin_manifest_list = yaml.safe_load((await _builtin_manifest_file.read()))
    else:
        _builtin_manifest_list = {}

    # Iterate each list and pop one of the dict keys to validate
    if tool_type == 'openai':
        for _schema in _manifest_list["tool_list"]:
            _parsed_schemas.append(
                {
                    "type": "function",
                    "function": _schema
                }
            )

        # Also append built-in tools if applicable
        if _builtin_manifest_list.get("builtin_tool_list"):
            for _builtin_schema in _builtin_manifest_list["builtin_tool_list"]:
                _parsed_schemas.append(
                    {
                        "type": "function",
                        "function": _builtin_schema
                    }
                )
    else:
        for _schema in _manifest_list["tool_list"]:
            _parsed_schemas.append(_schema)

        # Also append built-in tools if applicable
        if _builtin_manifest_list.get("builtin_tool_list"):
            for _builtin_schema in _builtin_manifest_list["builtin_tool_list"]:
                _parsed_schemas.append(_builtin_schema)

    return _parsed_schemas

# Fetch non-builtin tool name
async def fetch_actual_tool_name(tool_api_name: str) -> str:
    # Check if tool manifest exists
    if not await aiofiles.os.path.exists(f"tools/apis/{tool_api_name}/manifest.yaml"):
        raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
    
    # Open the YAML
    async with aiofiles.open(f"tools/apis/{tool_api_name}/manifest.yaml") as _manifest_file:
        _manifest = yaml.safe_load((await _manifest_file.read()))
        return _manifest["tool_name"]

# For APIs
async def return_api_tools_object(tool_api_name: str, discord_message = None, discord_bot = None):
    if tool_api_name is None:
        return None

    try:
        _function_payload = importlib.import_module(f"tools.apis.{tool_api_name}.tool").Tools(
            discord_message=discord_message,
            discord_bot=discord_bot
        )
    except ModuleNotFoundError as e:
        logging.error("I cannot import the tool because the module is not found: %s", e)
        #raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
        return None
    
    return _function_payload

# For Built-in tools, compared to other methods, this one directly pulls tool functions from tools.builtin regardless of tool selection
async def return_builtin_tool_object(function_name: str, discord_message = None, discord_bot = None):
    try:
        _function_payload = importlib.import_module(f"tools.builtin.{function_name}.tool").BuiltInTool(
            discord_message=discord_message,
            discord_bot=discord_bot
        )
    except ModuleNotFoundError as e:
        logging.error("I cannot import the tool because the module is not found: %s", e)
        #raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
        return None
    
    return _function_payload
