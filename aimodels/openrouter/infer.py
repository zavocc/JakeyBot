# TODO: KEEP THE BASE64 FORMAT REGARDLES
from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from core.ai.history import History as typehint_History
from os import environ
import base64
import copy
import discord
import json
import logging
import openai

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

        # Check if _openai_client_openrouter attribute is set
        if not hasattr(discord_bot, "_openai_client_openrouter"):
            raise Exception("OpenAI client for OpenRouter is not initialized, please check the bot initialization")
        
        # Check if OpenRouter API key is set
        if not environ.get("OPENROUTER_API_KEY"):
            raise ModelAPIKeyUnset("No OpenRouter API key was set, this model isn't available")

        self._guild_id = guild_id
        self._openai_client: openai.AsyncOpenAI = discord_bot._openai_client_openrouter


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
        self._model_name = (await db_conn.get_key(guild_id=self._guild_id, key="default_openrouter_model"))

        # Indicate the model name
        logging.info("Using OpenRouter model: %s", self._model_name)

        # Fetch tool
        _Tool = await self._fetch_tool(db_conn)

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
            _tempChatThread = copy.deepcopy(_chat_thread)
            _tempChatThread.append(_prompt)
            _one_off_chat_thread = _tempChatThread
        else:
            _chat_thread.append(_prompt)
            _one_off_chat_thread = _chat_thread

        # Set the reasoning tokens to medium
        if any(_miscmodels in self._model_name for _miscmodels in [":thinking", "gemini-2.5-pro"]):
            self._genai_params["extra_body"]["reasoning"] = {
                "max_tokens": 1200,
            }
        elif any(_miscmodels in self._model_name for _miscmodels in ["openai/o", "x-ai/grok-3-beta", "openai/codex"]):
            if not "mini-high" in self._model_name:
                self._genai_params["extra_body"]["reasoning"] = {
                    "effort": "medium",
                    "exclude": True 
                }

        _response = await self._openai_client.chat.completions.create(
            model=self._model_name,
            messages=_one_off_chat_thread,
            tools=_Tool["tool_schema"],
            **self._genai_params
        )

        # Remove references
        _one_off_chat_thread = None

        # Remove file attachments from prompt before saving to history
        if hasattr(self, "_file_data"):        
            # Delete the temporary chat thread to prevent memory leaks
            del _tempChatThread

            # Create a clean copy of the prompt without file attachments
            _clean_prompt = {
                "role": _prompt["role"],
                "content": [
                    _content for _content in _prompt["content"] 
                    if _content.get("type") == "text"
                ]
            }

            # Add a system notice about file processing that file was processed
            _clean_prompt["content"].append({
                "type": "text",
                "text": "[<system_notice>File attachment processed but removed from history. DO NOT make stuff up about it! Ask the user to reattach for more details</system_notice>]"
            })

            # Append the clean prompt to chat thread
            _chat_thread.append(_clean_prompt)

            # Clean up the file data to free memory
            del self._file_data


        # Agentic experiences
        # Begin inference operation
        _interstitial = None
        _toolUseErrorOccurred = False
        while True:
            # Check for tools
            if _response.choices[0].message.tool_calls:
                if not _interstitial:
                    _interstitial = await self._discord_method_send("▶️ Coming up with the plan...")

                # Append the chat history
                _chat_thread.append(_response.choices[0].message.model_dump())

                # Send text message if needed
                if _response.choices[0].message.content:
                    await Utils.send_ai_response(self._discord_ctx, prompt, _response.choices[0].message.content, self._discord_method_send)

                # Execute tools
                _toolCalls = _response.choices[0].message.tool_calls
                _toolParts = []
                for _tool in _toolCalls:
                    await _interstitial.edit(f"▶️ Executing tool: **{_tool.function.name}**")

                    if hasattr(_Tool["tool_object"], "_tool_function"):
                        _toExec = getattr(_Tool["tool_object"], "_tool_function")
                    elif hasattr(_Tool["tool_object"], f"_tool_function_{_tool.function.name}"):
                        _toExec = getattr(_Tool["tool_object"], f"_tool_function_{_tool.function.name}")
                    else:
                        logging.error("I think I found a problem related to function calling or the tool function implementation is not available: %s")
                        raise CustomErrorMessage("⚠️ An error has occurred while calling tools, please try again later or choose another tool")
            
                    # Execute tools
                    try:
                        _toolResult = {"toolResult": await _toExec(**json.loads(_tool.function.arguments))}
                    except Exception as e:
                        logging.error("Something when calling specific tool lately, reason: %s", e)
                        _toolResult = {"error": f"⚠️ Something went wrong while executing the tool: {e}\nTell the user about this error"}

                        # Must not set status to true if it was already set to False
                        if not _toolUseErrorOccurred:
                            _toolUseErrorOccurred = True

                    _toolParts.append({
                        "role": "tool",
                        "tool_call_id": _tool.id,
                        "content": str(_toolResult)
                    })

            # Re-run the request after tool call
            if _interstitial and _toolParts:
                # Edit interstitial message
                if not _toolUseErrorOccurred:
                    await _interstitial.edit(f"✅ Used: **{_Tool['tool_human_name']}**")
                else:
                    await _interstitial.edit(f"⚠️ Error executing tool: **{_Tool['tool_human_name']}**")

                # Append the tool call result to the chat thread
                _chat_thread.extend(_toolParts)

                # Re-run the request
                _response = await self._openai_client.chat.completions.create(
                    model=self._model_name,
                    messages=_chat_thread,
                    tools=_Tool["tool_schema"],
                    **self._genai_params
                )

            # If the response has tool calls, re-run the request
            if not _response.choices[0].message.tool_calls:
                # Send final message in this condition since the agent is not looping anymore
                if _response.choices[0].message.content:
                    await Utils.send_ai_response(self._discord_ctx, prompt, _response.choices[0].message.content, self._discord_method_send)
                break

        # Send message what model used
        await self._discord_method_send(f"-# Using OpenRouter model: **{self._model_name}**")

        # Append the response to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
