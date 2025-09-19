from core.exceptions import CustomErrorMessage
from enum import Enum
from tools import ToolUseInstance
import discord as typehint_Discord
import json
import logging

class ReasoningType(Enum):
    OPENAI_GOOGLE = "openai"
    OPENROUTER = "openrouter"
    ANTHROPIC_COMPAT = "anthropic"

class OpenAIUtils:
    # Normalize reasoning
    def parse_reasoning(self, model_id: str, reasoning_type: ReasoningType) -> dict:
        _constructed_params = {
            "extra_body": {},
        }

        # If the model reasoning uses OpenAI-style reasoning syntax
        if reasoning_type == "openai":
            # if model ID has "-minimal" at the end
            if model_id.endswith("-minimal"):
                _constructed_params["reasoning_effort"] = "minimal"
            elif model_id.endswith("-medium"):
                _constructed_params["reasoning_effort"] = "medium"
            elif model_id.endswith("-high"):
                _constructed_params["reasoning_effort"] = "high"
            else:
                _constructed_params["reasoning_effort"] = "low"

            # Set max_completion_tokens
            _constructed_params["max_completion_tokens"] = 32000

        # This is specific for OpenRouter hosted models
        elif reasoning_type == "openrouter":
            _constructed_params["extra_body"]["reasoning"] = {"max_tokens": 4096}
            if model_id.endswith("-minimal"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 128
            elif model_id.endswith("-medium"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 12000
            elif model_id.endswith("-high"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 24000

        # This is specific for Anthropic hosted models
        elif reasoning_type == "anthropic":
            _constructed_params["extra_body"]["thinking"] = {"type": "enabled", "budget_tokens": 4096}
            if model_id.endswith("-minimal"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 128
            elif model_id.endswith("-medium"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 12000
            elif model_id.endswith("-high"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 24000

        return _constructed_params

    # Handle multimodal
    # Remove one per image restrictions so we'll just
    async def upload_files(self, attachment: typehint_Discord.Attachment, extra_metadata: str = None):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

        if not hasattr(self, "uploaded_files"):
            self.uploaded_files = []

        self.uploaded_files.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": attachment.url
                }
            }
        )

        # Check for extra metadata
        if extra_metadata:
            self.uploaded_files.append(
                {
                    "type": "text",
                    "text": extra_metadata
                }
            )

    # Tool Runs
    # Process Tools
    async def load_tools(self):
        _tool_name = await self.db_conn.get_key(self.user_id, "tool_use")

        # TODO: Add proper checks if it's MCP so we can add attribute self.used_mcp = True
        # And to use mcp_check utility function

        # For models to read the available tools to be executed
        self.tool_state = ToolUseInstance()

        # Initialize MCP client if needed
        await self.tool_state.init_fastmcp_client(mcp_url=(await self.tool_state.determine_mcp_url(_tool_name)))
        self.tool_schema: list = await self.tool_state.fetch_and_load_tool_schema(_tool_name, tool_type="openai")

        # Tool class object containing all functions
        if not (await self.tool_state.mcp_check()):
            self.tool_object_payload: object = await self.tool_state.return_tool_object(_tool_name, discord_context=self.discord_context, discord_bot=self.discord_bot)

    # Runs tools and outputs parts
    async def execute_tools(self, tool_calls: list) -> list:
        _tool_parts = []
        for _tool_call in tool_calls:
            await self.discord_context.channel.send(f"> -# Using: ***{_tool_call.function.name}***")

            # Check if we can use MCP
            if (await self.tool_state.mcp_check()):
                try:
                    _tool_result = {"api_result": (await self.tool_state.execute_mcp_tool(_tool_call.function.name, json.loads(_tool_call.function.arguments)))}
                except Exception as e:
                    logging.error("An error occurred while calling remote tool function: %s", e)
                    _tool_result = {"error": f"⚠️ Something went wrong while executing the tool: {e}"}

            else:
                if hasattr(self.tool_object_payload, f"tool_{_tool_call.function.name}"):
                    _func_payload = getattr(self.tool_object_payload, f"tool_{_tool_call.function.name}")
                else:
                    logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s")
                    raise CustomErrorMessage("⚠️ An error has occurred while performing action, try choosing another tools to continue.")

                # Call the tools
                try:
                    _tool_result = {"api_result": await _func_payload(**json.loads(_tool_call.function.arguments))}
                except Exception as e:
                    logging.error("An error occurred while calling tool function: %s", e)
                    _tool_result = {"error": f"⚠️ Something went wrong while executing the tool: {e}"}

            _tool_parts.append({
                "role": "tool",
                "tool_call_id": _tool_call.id,
                "content": json.dumps(_tool_result)
            })

        # Return the parts
        return _tool_parts
