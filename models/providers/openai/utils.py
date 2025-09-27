from core.exceptions import CustomErrorMessage
from tools.utils import fetch_tool_schema, return_tool_object
from typing_extensions import Literal
import discord as typehint_Discord
import json
import logging

class OpenAIUtils:
    # Normalize reasoning
    def parse_reasoning(self, model_id: str, reasoning_type: Literal["openai", "openrouter-int", "anthropic"]) -> dict:
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

            # Log
            logging.info("Using OpenAI-style reasoning with effort: %s", _constructed_params["reasoning_effort"])

        # This is specific for OpenRouter hosted models
        # Only for models like Anthropic and Google
        elif reasoning_type == "openrouter-int":
            # Set the default to low
            _constructed_params["extra_body"]["reasoning"] = {"enabled": True, "max_tokens": 4096}

            # Check for suffixes
            if model_id.endswith("-minimal"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 128
            elif model_id.endswith("-medium"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 12000
            elif model_id.endswith("-high"):
                _constructed_params["extra_body"]["reasoning"]["max_tokens"] = 24000

            # Log
            logging.info("Using OpenRouter-style reasoning with effort value %d", _constructed_params["extra_body"]["reasoning"]["max_tokens"])

        # This is specific for Anthropic hosted models
        elif reasoning_type == "anthropic":
            # Set the default to low
            _constructed_params["extra_body"]["thinking"] = {"type": "enabled", "budget_tokens": 4096}

            # Check for suffixes
            if model_id.endswith("-minimal"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 128
            elif model_id.endswith("-medium"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 12000
            elif model_id.endswith("-high"):
                _constructed_params["extra_body"]["thinking"]["budget_tokens"] = 24000

            # Log
            logging.info("Using Anthropic-style reasoning with budget_tokens value %d", _constructed_params["extra_body"]["thinking"]["budget_tokens"])

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


        # For models to read the available tools to be executed
        self.tool_schema: list = await fetch_tool_schema(_tool_name, tool_type="openai")

        # Tool class object containing all functions
        self.tool_object_payload: object = await return_tool_object(_tool_name, discord_context=self.discord_context, discord_bot=self.discord_bot)

    # Runs tools and outputs parts
    async def execute_tools(self, tool_calls: list) -> list:
        _tool_parts = []
        for _tool_call in tool_calls:
            await self.discord_context.channel.send(f"> -# Using: ***{_tool_call.function.name}***")

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
                _tool_result = {"error": f"⚠️ Something went wrong while executing the tool: {e}\nTell the user about this error"}

            _tool_parts.append({
                "role": "tool",
                "tool_call_id": _tool_call.id,
                "content": json.dumps(_tool_result)
            })

        # Return the parts
        return _tool_parts
