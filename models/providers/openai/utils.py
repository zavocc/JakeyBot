from core.exceptions import CustomErrorMessage
from models.chat_utils import upload_blob_storage
from tools.utils import fetch_tool_schema, return_tool_object
from os import environ
from pathlib import Path
import aiofiles
import aiofiles.os
import discord as typehint_Discord
import json
import logging
import random

class OpenAIUtils:
    # Handle multimodal
    # Remove one per image restrictions so we'll just
    async def upload_files(self, attachment: typehint_Discord.Attachment, extra_metadata: str = None):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

        if not hasattr(self, "uploaded_files"):
            self.uploaded_files = []

        if hasattr(self.discord_bot, "aiohttp_instance"):
            _aiohttp_session = self.discord_bot.aiohttp_instance
        else:
            logging.warning("No aiohttp_instance found in discord bot, aborting")
            raise CustomErrorMessage("⚠️ An error has occurred while processing the file, please try again later.")

        _tempdir = Path(environ.get("TEMP_DIR", "temp"))
        _tempdir.mkdir(parents=True, exist_ok=True)
        _filename = _tempdir / f"JAKEY.{random.randint(518301839, 6582482111)}.{attachment.filename}"

        try:
            async with _aiohttp_session.get(attachment.url, allow_redirects=True) as file_dl:
                if file_dl.status >= 400:
                    raise CustomErrorMessage("⚠️ Failed to download the attachment, please try again later.")

                async with aiofiles.open(_filename, "wb") as filepath:
                    async for _chunk in file_dl.content.iter_chunked(8192):
                        await filepath.write(_chunk)

            async with aiofiles.open(_filename, "rb") as filepath:
                _file_bytes = await filepath.read()

            _blob_url = await upload_blob_storage(_filename.name, _file_bytes)
        finally:
            if _filename.exists():
                await aiofiles.os.remove(_filename)

        self.uploaded_files.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _blob_url
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
