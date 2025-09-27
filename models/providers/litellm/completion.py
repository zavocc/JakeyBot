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

        # Model config
        _model_params: typehint_ModelParams = typehint_ModelParams()
        self.model_params: dict = _model_params.model_dump()

        # User ID
        self.user_id: int = user_id

        # Database
        self.db_conn: typehint_History = db_conn or None
        
    # Chat
    async def send_message(self, prompt: str, chat_history: list = None, system_instructions: str = None):
        # Props used:
        # model_id -> required, str
        # enable_tools -> true or false
        # has_reasoning -> required, true or false
        # reasoning_type -> simple or advanced

        # Load chat history and system instructions
        if chat_history is None or type(chat_history) != list:
            chat_history = []
            if self.model_props.enable_system_instructions and system_instructions:
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

        # Normalize reasoning
        if self.model_props.has_reasoning:
            # Parse reasoning and get constructed params
            _reasoning_params = self.parse_reasoning(self.model_props.model_id, self.model_props.reasoning_type)
            
            # Update model_params with reasoning parameters
            self.model_params.update(_reasoning_params)
            self.model_params.pop("max_tokens", None) # Remove max tokens if present
            
            # Strip any suffixes "-minimal", "-low", "-medium", "-high"
            self.model_props.model_id = self.model_props.model_id.replace("-minimal", "").replace("-low", "").replace("-medium", "").replace("-high", "")
        # For reasoning disabled
        else:
            # If the model ID has any suffix but reasoning is disabled, raise error
            if any(self.model_props.model_id.endswith(_rsning_suffix) for _rsning_suffix in ["-minimal", "-low", "-medium", "-high"]):
                logging.error("Model ID has reasoning suffix but reasoning disabled: %s", self.model_props.model_id)
                raise CustomErrorMessage("⚠️ The selected model requires reasoning to be enabled. But it has not been configured, please select other models.")
            
            logging.info("Reasoning is disabled, setting reasoning_effort to null")
            # Disable reasoning effort
            self.model_params["reasoning_effort"] = None

        # Check for tools
        if self.model_props.enable_tools:
            await self.load_tools()
            self.model_params["tools"] = self.tool_schema

        # Get response
        if not self.model_props.model_id:
            raise ValueError("Model is required, chose nothing")
        
        # Drop unnecessary params
        litellm.drop_params = True
        _response = await litellm.acompletion(
            model=self.model_props.model_id,
            messages=chat_history,
            **self.model_params
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
                    **self.model_params
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