from core.exceptions import CustomErrorMessage
import discord as typehint_Discord
import importlib
import json
import logging

class OpenAIUtils:
    # Handle multimodal
    # Remove one per image restrictions so we'll just
    async def upload_files(self, attachment: typehint_Discord.Attachment):
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

    # Tool Runs
    # Process Tools
    async def load_tools(self):
        _tool_name = await self.db_conn.get_key(self.user_id, "tool_use")
        if _tool_name is None:
            _function_payload = None
        else:
            # Tool CodeExecution is not supported
            if _tool_name == "CodeExecution":
                logging.error("CodeExecution tool is not supported.")
                raise CustomErrorMessage("⚠️ CodeExecution is not available for this model. Please choose another model to continue")

            try:
                _function_payload = importlib.import_module(f"tools.{_tool_name}").Tool(
                    method_send=self.discord_context.channel.send,
                    discord_ctx=self.discord_context,
                    discord_bot=self.discord_bot
                )
            except ModuleNotFoundError as e:
                logging.error("I cannot import the tool because the module is not found: %s", e)
                raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
            
        # Get the schemas
        if _function_payload:
            if type(_function_payload.tool_schema_openai) == list:
                _tool_schema = _function_payload.tool_schema_openai
            else:
                _tool_schema = [_function_payload.tool_schema_openai]
        else:
            _tool_schema = None

        # For models to read the available tools to be executed
        self.tool_schema: list = _tool_schema

        # Pretty UI
        self.tool_human_name: str = _function_payload.tool_human_name

        # Tool class object containing all functions
        self.tool_object_payload: object = _function_payload

    # Runs tools and outputs parts
    async def execute_tools(self, tool_calls: list) -> list:
        _tool_parts = []
        for _tool_call in tool_calls:
            await self.discord_context.channel.send(f"> -# Using: ***{_tool_call.function.name}***")

            if hasattr(self.tool_object_payload, "_tool_function"):
                _func_payload = getattr(self.tool_object_payload, "_tool_function")
            elif hasattr(self.tool_object_payload, f"_tool_function_{_tool_call.function.name}"):
                _func_payload = getattr(self.tool_object_payload, f"_tool_function_{_tool_call.function.name}")
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
