from .utils import LiteLLMUtils
from core.database import History as typehint_History
from core.exceptions import CustomErrorMessage
from models.validation import ModelParamsOpenAIDefaults as typehint_ModelParams
from models.validation import ModelProps as typehint_ModelProps
from os import environ
import discord as typehint_Discord
import litellm
import logging
import models.core

class ChatSession(LiteLLMUtils):
    def __init__(self, 
                 user_id: int, 
                 model_props: typehint_ModelProps,
                 discord_bot: typehint_Discord.Bot = None,
                 discord_context: typehint_Discord.ApplicationContext = None,
                 db_conn: typehint_History = None,
                 client_name: str = None):
        # Discord bot object - needed for interactions with current state of Discord API
        self.discord_bot: typehint_Discord.Bot = discord_bot or None

        # For sending messages
        self.discord_context: typehint_Discord.ApplicationContext = discord_context or None

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
        if chat_history is None or type(chat_history) != list:
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
        
        # Additional model params
        # Log
        if self.model_props.additional_params:
            logging.info("Merging additional_params into model_params: %s", self.model_props.additional_params)

        # Reverse merge 
        _merged_params = self.model_props.additional_params.copy() if self.model_props.additional_params else {}

        # Remove model and messages if they exist in additional_params to avoid conflicts
        logging.info("Removing conflicting keys from additional_params if present")
        # Remove core conflicting keys
        _merged_params.pop("model", None)
        _merged_params.pop("messages", None)
        _merged_params.pop("tools", None)

        # Remove others found in model_params
        for _keys in self.model_params.keys():
            if _keys in _merged_params:
                logging.info("Removing key from additional_params to avoid conflict: %s", _keys)
                _merged_params.pop(_keys, None)

        # Update with model defaults
        _merged_params.update(self.model_params)
        logging.info("Final merged model parameters: %s", _merged_params)
        
        # Drop unnecessary params
        litellm.drop_params = True
        _response = await litellm.acompletion(
            model=self.model_props.model_id,
            messages=chat_history,
            **_merged_params
        )

        # Check for tool calls
        while True:
            # Initial check
            if _response.choices[0].message.tool_calls:
                # Append the chat history
                chat_history.append(_response.choices[0].message.model_dump(exclude_defaults=True, exclude_none=True, exclude_unset=True))

                # Tool calls
                _tool_calls = _response.choices[0].message.tool_calls

                # Tool parts
                _tool_parts = await self.execute_tools(_tool_calls)

                # Append the tool parts to chat history
                chat_history.extend(_tool_parts)

                # Run the response the second time
                _response = await litellm.acompletion(
                    model=self.model_props.model_id,
                    messages=chat_history,
                    **_merged_params
                )

            # Check if we need to run tools again, this block will stop the loop and send the response
            if not _response.choices[0].message.tool_calls:
                if _response.choices[0].message.content:
                    await models.core.send_ai_response(self.discord_context, prompt, _response.choices[0].message.content, self.discord_context.channel.send)
                break

        # Append to chat history
        chat_history.append(_response.choices[0].message.model_dump(exclude_defaults=True, exclude_none=True, exclude_unset=True))

        # Return the chat history
        return chat_history