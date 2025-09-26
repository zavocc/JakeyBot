from core.exceptions import CustomErrorMessage
from typing import Literal
import aiofiles
import aiofiles.os
import importlib
import logging
import yaml

# Fetch, parse, and validate tool schema
async def fetch_tool_schema(tool_name: str, tool_type: Literal['openai', 'google']) -> list:
    if tool_name is None:
        return None

    _parsed_schemas = []
    
    # Check if tool manifest exists
    if not (await aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml")):
        raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
    
    # Open the YAML
    async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
        _manifest_list = yaml.safe_load((await _manifest_file.read()))

    # if the manifest is empty list, raise error
    if not _manifest_list.get("tool_list"):
        raise CustomErrorMessage("⚠️ The agent you selected is currently misconfigured, please choose another agent using `/agent` command")
    
    # Iterate each list and pop one of the dict keys to validate
    if tool_type == 'openai':
        for _schema in _manifest_list["tool_list"]:
            _parsed_schemas.append(
                {
                    "type": "function",
                    "function": _schema
                }
            )
    else:
        for _schema in _manifest_list["tool_list"]:
            _parsed_schemas.append(_schema)

    return _parsed_schemas

# Fetch tool name
async def fetch_actual_tool_name(tool_name: str) -> str:
    # Check if tool manifest exists
    if not await aiofiles.os.path.exists(f"tools/apis/{tool_name}/manifest.yaml"):
        raise CustomErrorMessage("⚠️ The agent you selected is currently unavailable, please choose another agent using `/agent` command")
    
    # Open the YAML
    async with aiofiles.open(f"tools/apis/{tool_name}/manifest.yaml") as _manifest_file:
        _manifest = yaml.safe_load((await _manifest_file.read()))
        return _manifest["tool_name"]


# For legacy tools that supports discord bot connection
async def return_tool_object(tool_name: str, discord_context = None, discord_bot = None):
    if tool_name is None:
        return None

    try:
        _function_payload = importlib.import_module(f"tools.apis.{tool_name}.tool").Tools(
            discord_ctx=discord_context,
            discord_bot=discord_bot
        )
    except ModuleNotFoundError as e:
        logging.error("I cannot import the tool because the module is not found: %s", e)
        raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
    
    return _function_payload