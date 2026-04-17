from .utils import LiteLLMUtils
from core.database import History as typehint_History

from models.validation import ModelParamsOpenAIDefaults as typehint_ModelParams
from models.validation import ModelProps as typehint_ModelProps

import discord as typehint_Discord
import litellm
import logging
import models.core

class ChatSession(LiteLLMUtils):
    def __init__(self,
                 user_id: int,
                 model_props: typehint_ModelProps,
                 discord_bot: typehint_Discord.Bot = None,
                 discord_message: typehint_Discord.Message = None,
                 db_conn: typehint_History = None,
                 client_name: str = None):
        # Discord bot object - needed for interactions with current state of Discord API
        self.discord_bot: typehint_Discord.Bot = discord_bot or None

        # For sending messages
        self.discord_message: typehint_Discord.Message = discord_message or None

        # LiteLLM doesn't support client_name
        if client_name:
            logging.warning("LiteLLM does not support client_name, ignoring the provided value")

        # Model properties
        try:
            # Check if model_props is already a ModelProps instance
            if isinstance(model_props, typehint_ModelProps):
                self.model_props = model_props
            else:
                # If it's a dict, create a new ModelProps instance
                self.model_props = typehint_ModelProps(**model_props)
        except Exception as e:
            logging.error("Invalid model_props provided: %s", e)
            raise ValueError(f"Invalid model_props: {e}")

        # Model params
        _model_params: typehint_ModelParams = typehint_ModelParams()
        self.model_params: dict = _model_params.model_dump()

        # User ID
        self.user_id: int = user_id

        # Database
        self.db_conn: typehint_History = db_conn or None

    # Chat
    async def send_message(self, prompt: str, chat_history: list = None, system_instructions: str = None):
        # Load chat history and system instructions
        if chat_history is None or type(chat_history) is not list:
            chat_history = []
            if self.model_props.enable_system_instruction and system_instructions:
                chat_history.append({
                    "role": "system",
                    "content": system_instructions
                })


        # Format the prompt
        _prep_prompt = {
            "role": "user",
            "content": []
        }

        # Check if we have an attachment
        if hasattr(self, "uploaded_files") and self.uploaded_files:
            # Add the attachment part to the prompt
            _prep_prompt["content"].extend(self.uploaded_files)
        
        # Append the actual prompt
        _prep_prompt["content"].append({
            "type": "text",
            "text": prompt,
        })

        # Add the prepared prompt to chat history
        chat_history.append(_prep_prompt)

        # Check for tools
        if self.model_props.enable_tools:
            await self.load_tools()
            self.model_params["tools"] = self.tool_schema

        # Get response
        if not self.model_props.model_id:
            raise ValueError("Model is required, chose nothing")
        
        # Merge additional model params with defaults.
        # Order matters: additional_params is loaded first, model_params overrides conflicts.
        _additional_params = self.model_props.additional_params or {}
        if _additional_params:
            logging.info("Merging additional_params into model_params: %s", _additional_params)
        _merged_params = {
            **_additional_params,
            **self.model_params,
        }
        logging.info("Final merged model parameters: %s", _merged_params)

        # Keep request-owned fields authoritative.
        _base_request_kwargs = {
            **_merged_params,
            "model": self.model_props.model_id,
        }
        
        # Drop unnecessary params
        litellm.drop_params = True
        _response = await litellm.acompletion(**{
            **_base_request_kwargs,
            "messages": chat_history,
        })

        # Check for tool calls
        while True:
            # Initial check
            if _response.choices[0].message.tool_calls:
                # Append the chat history
                chat_history.append(_response.choices[0].message.model_dump(exclude_defaults=True, exclude_none=True, exclude_unset=True))

                # Output text response if needed
                if _response.choices[0].message.content:
                    await models.core.send_ai_response(self.discord_message, prompt, _response.choices[0].message.content, self.discord_message.channel.send)

                # Tool calls
                _tool_calls = _response.choices[0].message.tool_calls

                # Tool parts
                _tool_parts = await self.execute_tools(_tool_calls)

                # Append the tool parts to chat history
                chat_history.extend(_tool_parts)

                # Run the response the second time
                _response = await litellm.acompletion(**{
                    **_base_request_kwargs,
                    "messages": chat_history,
                })

            # Check if we need to run tools again, this block will stop the loop and send the response
            if not _response.choices[0].message.tool_calls:
                if _response.choices[0].message.content:
                    await models.core.send_ai_response(self.discord_message, prompt, _response.choices[0].message.content, self.discord_message.channel.send)
                break

        # Append to chat history
        chat_history.append(_response.choices[0].message.model_dump(exclude_defaults=True, exclude_none=True, exclude_unset=True))

        # Return the chat history
        return chat_history
