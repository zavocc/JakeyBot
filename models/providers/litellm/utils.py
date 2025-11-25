from core.exceptions import CustomErrorMessage
from core.storage import get_storage_provider, StorageProvider
from models.chat_utils import upload_files_to_storage
from os import environ
from tools.utils import fetch_tool_schema, return_tool_object
from pathlib import Path
from uuid import uuid4
import aiofiles
import aiohttp
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

        # Test if we have "self.discord_bot.aiohttp_instance"
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Found aiohttp_instance in discord bot, using that for downloading the file")
            _aiohttp_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            # Raise exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot, aborting")
            raise CustomErrorMessage("⚠️ An error has occurred while processing the file, please try again later.")

        # Grab filename
        _filename = f"{environ.get('TEMP_DIR')}/JAKEY.{uuid4()}.{attachment.filename}"
        try:
            async with _aiohttp_session.get(attachment.url, allow_redirects=True) as file_dl:
                # write to file with random number ID
                async with aiofiles.open(_filename, "wb") as filepath:
                    async for _chunk in file_dl.content.iter_chunked(8192):
                        await filepath.write(_chunk)

            # Upload the file using modular storage provider
            _storage_provider = self._get_storage_provider()
            _blob_url = await upload_files_to_storage(
                file_path=_filename,
                file_name=Path(_filename).name,
                storage_provider=_storage_provider
            )
        except Exception as e:
            # Raise exception
            raise e
        finally:
            # Remove the file if it exists ensuring no data persists even on failure
            if Path(_filename).exists():
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

    def _get_storage_provider(self) -> StorageProvider:
        """
        Get the storage provider instance.
        
        Override this method to use a different storage provider.
        By default, uses Azure Blob Storage with the bot's blob service client.
        
        Returns:
            StorageProvider: The storage provider to use for file uploads.
        """
        # Check if bot has a custom storage provider
        if hasattr(self.discord_bot, "storage_provider"):
            return self.discord_bot.storage_provider
        
        # Default to Azure Blob Storage with bot's client
        if hasattr(self.discord_bot, "blob_service_client"):
            return get_storage_provider(
                "azure_blob",
                client=self.discord_bot.blob_service_client
            )
        
        # Fallback: create provider without client (will use env vars)
        return get_storage_provider("azure_blob")

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
