from .config import ModelParams
from models.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from os import environ
import discord
import json
import litellm
import logging
import re

class Completions(ModelParams):
    def __init__(self, model_name, discord_ctx, discord_bot, guild_id: int = None):
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

        if environ.get("ANTHROPIC_API_KEY"):
            self._model_name = "anthropic/" + model_name
        else:
            raise ModelAPIKeyUnset("No Anthropic API key was set, this model isn't available")
    
        self._guild_id = guild_id

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image or PDF
        if not "image" in attachment.content_type and not "pdf" in attachment.content_type:
            raise CustomErrorMessage("⚠️ This model only supports image or PDF attachments")

        if attachment.content_type.startswith("application/pdf"):
            self._file_data = [
                {
                    "type": "document",
                    "source": {
                        "type": "url",
                        "url": attachment.url
                    }
                }
            ]
        else:
            self._file_data = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": attachment.url
                    }
                }
            ]

    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        # Fetch tool
        _Tool = await self._fetch_tool(db_conn)

        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_instruction,
                        "cache_control": {
                            "type": "ephemeral"
                        }
                    }
                ] 
            }]

        # If '/cache:true' is in the prompt, we need to cache the prompt
        # Search must be either have whitespace or start/end of the string
        if re.search(r"(^|\s)/cache:true(\s|$)", prompt):
            await self._discord_method_send("ℹ️ Caching the prompt to improve performance later.")
            # Remove the '/cache:true' from the prompt
            prompt = re.sub(r"(^|\s)/cache:true(\s|$)", "", prompt)

            _cachePrompt = True
        else:
            _cachePrompt = False

        # Craft prompt
        _prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ]
        }

        # Check if we have an attachment
        if hasattr(self, "_file_data"):
            # Add the attachment part to the prompt
            _prompt["content"].extend(self._file_data)

        
        if _cachePrompt:
            # Add cache control to the message
            _prompt["content"][-1]["cache_control"] = {
                "type": "ephemeral"
            }

        _chat_thread.append(_prompt)

        # Generate completion
        litellm.api_key = environ.get("ANTHROPIC_API_KEY")
        if environ.get("LITELLM_DEBUG"):
            litellm._turn_on_debug()

        # First response which is called only once
        _response = await litellm.acompletion(
            model=self._model_name,
            messages=_chat_thread,
            tools=_Tool["tool_schema"],
            **self._genai_params
        )

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
                        _toolUseErrorOccurred = False
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
                if _toolUseErrorOccurred:
                    await _interstitial.edit(f"⚠️ Error executing tool: **{_Tool['tool_human_name']}**")
                else:
                    await _interstitial.edit(f"✅ Used: **{_Tool['tool_human_name']}**")

                # Append the tool call result to the chat thread
                _chat_thread.extend(_toolParts)

                # Re-run the request
                _response = await litellm.acompletion(
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

        # Done
        # Append the chat thread and send the status response
        _chat_thread.append(_response.choices[0].message.model_dump())
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)