from core.exceptions import CustomErrorMessage
from os import environ
from pathlib import Path
from tools.utils import fetch_tool_schema, return_api_tools_object, return_builtin_tool_object
from uuid import uuid4
import discord as typehint_Discord
import aiofiles
import aiohttp
import asyncio
import logging

class GoogleUtils:
    # Handle multimodal
    async def upload_files(self, attachment: typehint_Discord.Attachment, extra_metadata: str = None):
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
         # Sometimes mimetype has text/plain; charset=utf-8, we need to grab the first part
        _mimetype = attachment.content_type.split(";")[0]
        try:
            async with _aiohttp_session.get(attachment.url, allow_redirects=True) as file_dl:
                # write to file with random number ID
                async with aiofiles.open(_filename, "wb") as filepath:
                    async for _chunk in file_dl.content.iter_chunked(8192):
                        await filepath.write(_chunk)

            # Upload the file
            _filedata = await self.google_genai_client.aio.files.upload(
                file=_filename, 
                config={
                    "mime_type": _mimetype
                }
            )

            while _filedata.state == "PROCESSING":
                _filedata = await self.google_genai_client.aio.files.get(name=_filedata.name)
                await asyncio.sleep(2.5)
        except Exception as e:
            # Raise exception
            raise e
        finally:
            # Remove the file if it exists ensuring no data persists even on failure
            if Path(_filename).exists():
                await aiofiles.os.remove(_filename)

            # Close the temporary aiohttp session if we created one
            if not hasattr(self.discord_bot, "aiohttp_instance"):
                logging.info("Closing temporary aiohttp client session on models.providers.google.utils.GoogleUtils.upload_files")
                await _aiohttp_session.close()

        # Add to the uploaded files
        self.uploaded_files.append(
            {
                "file_data": {
                    "file_uri": _filedata.uri,
                    "mime_type": _mimetype
                }
            }
        )

        # Check for extra metadata
        if extra_metadata:
            self.uploaded_files.append(
                {
                    "text": extra_metadata
                }
            )

    # Tool Runs
    # Process Tools
    async def load_tools(self):
        _tool_name = await self.db_conn.get_key(self.user_id, "tool_use")

        # For models to read the available tools to be executed
        self.tool_schema: list = await fetch_tool_schema(_tool_name, tool_type="google")

        # Tool class object containing all functions
        self.tool_object_payload: object = await return_api_tools_object(_tool_name, discord_message=self.discord_message, discord_bot=self.discord_bot)

    # Runs tools and outputs parts
    async def execute_tools(self, name: str, arguments: str) -> list:
        _tool_parts = []
        # Reject tool calls when no schema is loaded to avoid hallucinated tools
        if not isinstance(getattr(self, "tool_schema", None), list) or not self.tool_schema:
            logging.critical("Attempted to call tools without a loaded schema nor proper initialization... THIS IS A SECURITY RISK! Therefore we stopped executing this tool: %s", name)
            _tool_parts.append(
                {
                    "function_response": {
                        "name": name,
                        "response": {
                            "error": "Tools and agents are not yet properly initialized. Please tell the user to activate any tools via the /agent slash command and try again."
                        }
                    }
                }
            )
            return _tool_parts

        # Check if the requested tool name is in the schema or hallucinated
        _tool_names = [
            _tool["name"] for _tool in self.tool_schema
            if isinstance(_tool, dict) and _tool.get("name")
        ]
        if name not in _tool_names:
            logging.critical("Attempted to call a tool that is not in the loaded tool schema: %s", name)
            raise CustomErrorMessage("🛑 The response is terminated due to an invalid tool call.")

        # Import builtin tool payload if applicable
        _builtin_tool_object_payload = await return_builtin_tool_object(name, discord_message=self.discord_message, discord_bot=self.discord_bot)

        # Execute tools
        # Check for payloads and presence of the function to determine the type of tool to call
        if self.tool_object_payload and hasattr(self.tool_object_payload, f"tool_{name}"):
            _func_payload = getattr(self.tool_object_payload, f"tool_{name}")

            # Show indicator if the user-selected tool is being used
            await self.discord_message.channel.send(f"> -# Using: ***{name}***")

        # Check if it's a built-in tool, hopefully, and don't show indicator since it's not an agentic tool
        elif hasattr(_builtin_tool_object_payload, f"tool_{name}"):
            _func_payload = getattr(_builtin_tool_object_payload, f"tool_{name}")

        # If all else fails
        else:
            logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s")
            raise CustomErrorMessage("⚠️ An error has occurred while trying to execute agent tools, try choosing another tools to continue.")

        # Call the tools
        try:
            _tool_result = {"api_result": await _func_payload(**arguments)}
        except Exception as e:
            logging.error("An error occurred while calling tool function: %s", e)
            _tool_result = {"error": f"⚠️ Something went wrong while executing the tool: {e}\nTell the user about this error"}

        # Append the parts
        _tool_parts.append(
            {
                "function_response": {
                    "name": name,
                    "response": _tool_result
                }
            }
        )

        # Return the parts
        return _tool_parts
