from core.exceptions import CustomErrorMessage
from tools.utils import fetch_tool_schema, return_builtin_tool_object, return_api_tools_object
import discord as typehint_Discord
import json
import logging

class LiteLLMUtils:
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
        self.tool_object_payload: object = await return_api_tools_object(_tool_name, discord_context=self.discord_context, discord_bot=self.discord_bot)

    # Runs tools and outputs parts
    async def execute_tools(self, tool_calls: list) -> list:
        _tool_parts = []
        for _tool_call in tool_calls:
            await self.discord_context.channel.send(f"> -# Using: ***{_tool_call.function.name}***")

            # Import builtin tool payload if applicable
            _builtin_tool_object_payload = await return_builtin_tool_object(_tool_call.function.name, discord_context=self.discord_context, discord_bot=self.discord_bot)

            if hasattr(self.tool_object_payload, f"tool_{_tool_call.function.name}"):
                _func_payload = getattr(self.tool_object_payload, f"tool_{_tool_call.function.name}")
            elif hasattr(_builtin_tool_object_payload, f"tool_{_tool_call.function.name}"):
                _func_payload = getattr(_builtin_tool_object_payload, f"tool_{_tool_call.function.name}")
            else:
                logging.error("I think I found a problem related to function calling or the tool function implementation is not available")
                raise CustomErrorMessage("⚠️ An error has occurred while trying to execute agent tools, try choosing another tools to continue.")

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
