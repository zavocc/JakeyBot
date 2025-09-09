from core.ai.history import History as typehint_History
from core.exceptions import CustomErrorMessage
from models.validation import ModelParamsOpenAIDefaults as typehint_ModelParams
from models.validation import ModelProps as typehint_ModelProps
from os import environ
import discord as typehint_Discord
import importlib
import logging
import openai

class ChatSession:
    def __init__(self, 
                 user_id: int, 
                 model_props: typehint_ModelProps,
                 openai_client: openai.Client = None,
                 discord_bot: typehint_Discord.Bot = None,
                 discord_context: typehint_Discord.ApplicationContext = None,
                 db_conn: typehint_History = None):
        
        # Discord bot object - needed for interactions with current state of Discord API
        self.discord_bot: typehint_Discord.Bot = discord_bot or None

        # For sending message
        self.discord_context: typehint_Discord.ApplicationContext = discord_context or None

        # OpenAI Client, for efficiency we can reuse the same client instance
        # Otherwise we create a new one
        self.openai_client: openai.AsyncClient = openai_client or openai.AsyncClient(api_key=environ.get("OPENAI_API_KEY"))

        # Model properties
        try:
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

    # Process Tools
    async def load_tools(self):
        _tool_name = self.db_conn.get_key(self.user_id, "tool_use")
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
            except ModuleNotFoundError:
                logging.error("I cannot import the tool because the module is not found: %s", e)
                raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
            
        # Get the schemas
        if _function_payload:
            if type(_function_payload.tool_schema_openai) == list:
                _tool_schema = _function_payload.tool_schema_openai
            else:
                _tool_schema = [_function_payload.tool_schema_openai]
        else:
            _tool_schema = None

        # For models to read the available tools to be executed
        self.tool_schema = _tool_schema

        # Pretty UI
        self.tool_human_name = _function_payload.tool_human_name

        # Tool class object containing all functions
        self.tool_object_payload = _function_payload.tool_object_payload

    # Handle multimodal
    # Remove one per image restrictions so we'll just
    async def upload_files(self, attachment: typehint_Discord.Message):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise CustomErrorMessage("⚠️ This model only supports image attachments")

        self.uploaded_files = []

        for _attachment_urls in attachment.attachments:
            self.uploaded_files.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _attachment_urls.url
                    }
                }
            )
        
    # Chat
    async def send_message(self, prompt: str, chat_history: list = None, system_instructions: str = None):
        # We will validate model_props dict each:
        # model_id -> required, str
        # enable_tools -> true or false
        # enable_files -> true or false
        # enable_threads -> true or false
        # has_reasoning -> required, true or false

        # Load chat history and system instructions
        # checks "enable_threads", if set false then this will be disabled
        if self.model_props.enable_threads:
            if chat_history is None and type(chat_history) != list:
                chat_history = []
                if system_instructions:
                    chat_history.append({
                        "role": "system",
                        "content": system_instructions
                    })
            else:
                chat_history = []

        # Format the prompt
        _prep_prompt = {
            "role": "user",
            "content": []
        }

        # Check if we have an attachment
        if hasattr(self, "_file_data"):
            if not self.model_props.enable_files:
                raise CustomErrorMessage("⚠️ This model does not support file attachments, please choose another model to continue")

             # Add the attachment part to the prompt
            _prep_prompt["content"].extend(self._file_data)
        
        # Append the actual prompt
        _prep_prompt["content"].append({
            "type": "text",
            "text": prompt,
        })

        # Normalize reasoning
        if self.model_props.has_reasoning:
            # If the model reasoning uses simple
            if self.model_props.reasoning_type == "simple":
                # if model ID has "-minimal" at the end
                if self.model_props.model_id.endswith("-minimal"):
                    self.model_params["reasoning_effort"] = "minimal"
                elif self.model_props.model_id.endswith("-medium"):
                    self.model_params["reasoning_effort"] = "medium"
                elif self.model_props.model_id.endswith("-high"):
                    self.model_params["reasoning_effort"] = "high"
                else:
                    self.model_params["reasoning_effort"] = "low"

            # This is specific for OpenRouter
            elif self.model_props.reasoning_type == "advanced":
            #TODO: NOT YET COMPLETE< THIS IS DRY





