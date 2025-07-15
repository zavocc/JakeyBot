from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage, ModelAPIKeyUnset
from os import environ
import discord
import json
import logging
import openai

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

        # Check if _openai_client attribute is set
        if not hasattr(discord_bot, "_openai_client"):
            raise Exception("OpenAI client is not initialized, please check the bot initialization")
        
        # Check if OpenRouter API key is set
        if not environ.get("OPENAI_API_KEY"):
            raise ModelAPIKeyUnset("No OpenAI API key was set, this model isn't available")
        
        # Model name
        self._model_name = model_name

        self._guild_id = guild_id
        self._openai_client: openai.AsyncOpenAI = discord_bot._openai_client

    async def input_files(self, attachment: discord.Attachment):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

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
                "content": system_instruction   
            }]

        
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

        _chat_thread.append(_prompt)

        # Check if the model starts with o
        if self._model_name.startswith("o"):
            if not any(self._model_name.startswith(_oprefix) for _oprefix in ["o1-preview", "o1-mini"]):
                # Check if the suffix has -high
                if self._model_name.endswith("-high"):
                    # Set reasoning effort to high
                    self._genai_params["reasoning_effort"] = "high"

                    # Remove the -high suffix from the model name
                    self._model_name = self._model_name.removesuffix("-high")
                    logging.info("Using reasoning model with high reasoning effort: %s", self._model_name)
                else:
                    # Set reasoning effort to medium
                    self._genai_params["reasoning_effort"] = "medium"
                    logging.info("Using reasoning model with medium reasoning effort: %s", self._model_name)

            # Always set temperature to 1 for reasoning models
            self._genai_params["temperature"] = 1

        _response = await self._openai_client.chat.completions.create(
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
                _chat_thread.append(_response.choices[0].message.model_dump(exclude_unset=True))

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

        # Append the final output to chat thread and send the response
        _chat_thread.append(_response.choices[0].message.model_dump(exclude_unset=True))
        return {"response":"OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
