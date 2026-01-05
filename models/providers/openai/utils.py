from core.exceptions import CustomErrorMessage
from models.chat_utils import upload_files_blob
from os import environ
from tools.utils import fetch_tool_schema, return_builtin_tool_object, return_api_tools_object
from pathlib import Path
from uuid import uuid4
import aiofiles
import aiohttp
import discord as typehint_Discord
import json
import logging

class OpenAIUtils:
    # Handle multimodal
    # Remove one per image restrictions so we'll just
    async def upload_files(self, attachment: typehint_Discord.Attachment, extra_metadata: str = None, or_beta_openai_pdf_uploads_enabled: bool = False, or_beta_video_uploads_enabled: bool = False):
        _content_type = attachment.content_type or ""
        _is_pdf = _content_type == "application/pdf"
        _is_video = _content_type.startswith("video/")
        _is_image = _content_type.startswith("image/")

        if _is_pdf:
            if not or_beta_openai_pdf_uploads_enabled:
                raise CustomErrorMessage("⚠️ This model only supports image attachments")
            logging.info("Using PDF attachment with beta PDF upload support enabled")
        elif _is_video:
            if not or_beta_video_uploads_enabled:
                raise CustomErrorMessage("⚠️ This model only supports image attachments")
            logging.info("Using Video attachment with beta video upload support enabled")
        elif not _is_image:
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

            # Upload the file to blob storage
            _blob_url = await upload_files_blob(file_path=_filename, file_name=Path(_filename).name, blob_service_client=self.discord_bot.blob_service_client)
        except Exception as e:
            # Raise exception
            raise e
        finally:
            # Remove the file if it exists ensuring no data persists even on failure
            if Path(_filename).exists():
                await aiofiles.os.remove(_filename)

            # Close the temporary aiohttp session if we created one
            if not hasattr(self.discord_bot, "aiohttp_instance"):
                logging.info("Closing temporary aiohttp client session on models.providers.openai.utils.OpenAIUtils.upload_files")
                await _aiohttp_session.close()

        # Test if we have "self.discord_bot.aiohttp_instance"
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Found aiohttp_instance in discord bot, using that for downloading the file")
            _aiohttp_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            # Raise exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot, aborting")
            raise CustomErrorMessage("⚠️ An error has occurred while processing the file, please try again later.")


        # Check if it's image, video, or pdf and append accordingly
        if _is_pdf:
            self.uploaded_files.append(
                {
                    "type": "file",
                    "file": {
                        "filename": attachment.filename,
                        "file_data": _blob_url
                    }
                }
            )
        elif _is_video:
            self.uploaded_files.append(
                {
                    "type": "video_url",
                    "video_url": {
                        "url": _blob_url
                    }
                }
            )
        else:  # Image
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
        self.tool_object_payload: object = await return_api_tools_object(_tool_name, discord_message=self.discord_message, discord_bot=self.discord_bot)

    # Runs tools and outputs parts
    async def execute_tools(self, tool_calls: list) -> list:
        _tool_parts = []
        for _tool_call in tool_calls:
            # Reject tool calls when no schema is loaded and to avoid executing hallucinated tools
            if not isinstance(getattr(self, "tool_schema", None), list) or not self.tool_schema:
                logging.critical("Attempted to call tools without a loaded schema nor proper initialization... THIS IS A SECURITY RISK! Therefore we stopped executing this tool: %s", _tool_call.function.name)
                _tool_parts.append({
                    "role": "tool",
                    "tool_call_id": _tool_call.id,
                    "content": "Tools and agents are not yet properly initialized. Please tell the user to activate any tools via the /agent slash command and try again."
                })
                continue

            # Check if the requested tool name is in the schema or hallucinated
            _tool_names = [
                _tool.get("name") or _tool.get("function", {}).get("name")
                for _tool in self.tool_schema
                if isinstance(_tool, dict) and (_tool.get("name") or _tool.get("function", {}).get("name"))
            ]
            if _tool_call.function.name not in _tool_names:
                logging.critical("Attempted to call a tool that is not in the loaded tool schema: %s", _tool_call.function.name)
                raise CustomErrorMessage("🛑 The response is terminated due to an invalid tool call.")

            # Import builtin tool payload if applicable
            _builtin_tool_object_payload = await return_builtin_tool_object(_tool_call.function.name, discord_message=self.discord_message, discord_bot=self.discord_bot)

            # Execute tools
            # Check for payloads and presence of the function to determine the type of tool to call
            if self.tool_object_payload and hasattr(self.tool_object_payload, f"tool_{_tool_call.function.name}"):
                _func_payload = getattr(self.tool_object_payload, f"tool_{_tool_call.function.name}")

                # Show indicator if the user-selected tool is being used
                await self.discord_message.channel.send(f"> -# Using: ***{_tool_call.function.name}***")

            # Check if it's a built-in tool, hopefully, and don't show indicator since it's not an agentic tool
            elif hasattr(_builtin_tool_object_payload, f"tool_{_tool_call.function.name}"):
                _func_payload = getattr(_builtin_tool_object_payload, f"tool_{_tool_call.function.name}")

            # If all else fails
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
