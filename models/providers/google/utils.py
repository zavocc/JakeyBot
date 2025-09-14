from core.exceptions import CustomErrorMessage
from os import environ
from pathlib import Path
import discord as typehint_Discord
import aiofiles
import aiohttp
import asyncio
import importlib
import logging
import random

class GoogleUtils:
    #typehint
    #import google.genai as google_genai
    #google_genai_client: google_genai.Client = None

    # Normalize reasoning
    def parse_reasoning(self, model_id: str) -> dict:
        _constructed_params = {
            "thinkingConfig": {},
        }

        # if model ID has "-minimal" at the end
        if model_id.endswith("-minimal"):
            _constructed_params["thinkingConfig"]["thinking_budget"] = 128
        elif model_id.endswith("-medium"):
            _constructed_params["thinkingConfig"]["thinking_budget"] = 12000
        elif model_id.endswith("-high"):
            _constructed_params["thinkingConfig"]["thinking_budget"] = 24000
        else:
            _constructed_params["thinkingConfig"]["thinking_budget"] = 6000

        return _constructed_params

    # Handle multimodal
    async def upload_files(self, attachment: typehint_Discord.Attachment, extra_metadata: str = None):
        if not hasattr(self, "uploaded_files"):
            self.uploaded_files = []

        # Test if we have "self.discord_bot.aiohttp_instance"
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Found aiohttp_instance in discord bot, using that for downloading the file")
            _aiohttp_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.info("aiohttp_instance not found in discord bot, creating a temporary aiohttp client session")
            _aiohttp_session = aiohttp.ClientSession()

        # Grab filename
        _filename = f"{environ.get('TEMP_DIR')}/JAKEY.{random.randint(518301839, 6582482111)}.{attachment.filename}"
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
            if type(_function_payload.tool_schema) == list:
                _tool_schema = _function_payload.tool_schema
            else:
                _tool_schema = [_function_payload.tool_schema]
        else:
            _tool_schema = None

        # For models to read the available tools to be executed
        self.tool_schema: list = _tool_schema

        # Tool class object containing all functions
        self.tool_object_payload: object = _function_payload

    # Runs tools and outputs parts
    async def execute_tools(self, name: str, arguments: str) -> list:
        _tool_parts = []
        await self.discord_context.channel.send(f"> -# Using: ***{name}***")

        # Execute tools
        if hasattr(self.tool_object_payload, "_tool_function"):
            _func_payload = getattr(self.tool_object_payload, "_tool_function")
        elif hasattr(self.tool_object_payload, f"_tool_function_{name}"):
            _func_payload = getattr(self.tool_object_payload, f"_tool_function_{name}")
        else:
            logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s")
            raise CustomErrorMessage("⚠️ An error has occurred while performing action, try choosing another tools to continue.")

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
