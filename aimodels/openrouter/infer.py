from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from core.ai.history import History as typehint_History
from os import environ
import base64
import discord
import gc
import litellm
import logging

class Completions(ModelParams):
    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = None):
        super().__init__()

        # Discord context
        self._discord_ctx = discord_ctx

        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = self._discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = self._discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        # Check if discord_bot whether if its a subclass of discord.Bot
        if not isinstance(discord_bot, discord.Bot):
            raise Exception("Invalid discord bot object provided")
        
        # Discord bot object lifecycle instance
        self._discord_bot: discord.Bot = discord_bot

        if not environ.get("OPENROUTER_API_KEY"):
            raise ModelAPIKeyUnset("No OpenRouter API key was set, this model isn't available")

        self._guild_id = guild_id


    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image
        if not "image" in attachment.content_type and not "pdf" in attachment.content_type:
            raise CustomErrorMessage("⚠️ This model only supports image or PDF attachments")

        # Check if attachment size is more than 3MB in which reject it
        if attachment.size > 3 * 1024 * 1024:
            raise CustomErrorMessage("⚠️ Attachment size exceeds 3MB limit")
        
        # Encode the attachment data to base64
        _encoded_data = base64.b64encode(await attachment.read()).decode('utf-8')

        # Create a data url
        _dataurl = f"data:{attachment.content_type};base64,{_encoded_data}"

        if attachment.content_type.startswith("application/pdf"):
            self._file_data = [
                {
                    "type": "file",
                    "file": {
                        "filename": attachment.filename,
                        "file_data": _dataurl
                    }
                }
            ]
        else:
            self._file_data = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _dataurl
                    }
                }
            ]

    async def chat_completion(self, prompt, db_conn: typehint_History, system_instruction: str = None):
        # Before we begin, get the OpenRouter model name and override self._model_name
        self._model_name = "openrouter/" + (await db_conn.get_key(guild_id=self._guild_id, key="default_openrouter_model"))

        # Indicate the model name
        logging.info("Using OpenRouter model: %s", self._model_name)

        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": system_instruction
                }]
            }]

            # If it's from Anthropic, also append "cache_control" block to system prompt
            if "claude-" in self._model_name:
                _chat_thread[-1]["content"][0]["cache_control"] = {
                    "type": "ephemeral"
                }


        # Craft prompt
        _prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }

        # Check if we have an attachment
        if hasattr(self, "_file_data"):
            # Add the attachment part to the prompt
            _prompt["content"].extend(self._file_data)


        # Temporary chat thread
        _tempChatThread = _chat_thread.copy()
        _tempChatThread.append(_prompt)

        # Params
        litellm.api_key = environ.get("OPENROUTER_API_KEY")
        if environ.get("LITELLM_DEBUG"):
            litellm._turn_on_debug()

        # Set the reasoning tokens to medium
        if any(_miscmodels in self._model_name for _miscmodels in [":thinking", "gemini-2.5-pro"]):
            self._genai_params["extra_body"]["reasoning"] = {
                "max_tokens": 1200,
            }
        elif any(_miscmodels in self._model_name for _miscmodels in ["openai/o", "x-ai/grok-3-beta"]):
            self._genai_params["extra_body"]["reasoning"] = {
                "effort": "medium",
                "exclude": True 
            }


        # Generate completion
        _response = await litellm.acompletion(messages=_tempChatThread, model=self._model_name, **self._genai_params)

        # Delete the temporary chat thread to prevent memory leaks
        del _tempChatThread

        # Remove file attachments from prompt before saving to history
        if hasattr(self, "_file_data"):
            # Filter out image_url and file content types, keep only text
            _prompt["content"] = [
                _content for _content in _prompt["content"] 
                if _content.get("type") == "text"
            ]
            # Add a note that file was processed
            _prompt["content"].append({
                "type": "text",
                "text": "[<system_notice>File attachment processed but removed from history. DO NOT make stuff up about it! Ask the user to reattach for more details</system_notice>]"
            })
            # Clean up the file data to free memory
            del self._file_data

        # TODO: remove this
        _objects_cleaned = gc.collect()
        logging.info("Cleaned %s objects", _objects_cleaned)

        # Append the cleaned prompt to the chat thread
        _chat_thread.append(_prompt)

        # Append the response to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        # Send message what model used
        await self._discord_method_send(f"-# Using OpenRouter model: **{self._model_name}**")

        # Send the response
        await Utils.send_ai_response(self._discord_ctx, prompt, _response.choices[0].message.content, self._discord_method_send)
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
