from .utils import GoogleUtils
from core.config import config
from core.database import History as typehint_History
from core.exceptions import CustomErrorMessage
from models.validation import ModelParamsGeminiDefaults as typehint_ModelParams
from models.validation import ModelProps as typehint_ModelProps
import discord
import io
import logging
import google.genai as google_genai
import google.genai.errors as google_genai_errors
import google.genai.types as google_genai_types
import models.core

class ChatSession(GoogleUtils):
    def __init__(self, 
                 user_id: int, 
                 model_props: typehint_ModelProps,
                 discord_bot: discord.Bot = None,
                 discord_context: discord.ApplicationContext = None,
                 db_conn: typehint_History = None,
                 client_name: str = None):
        # Discord bot object - needed for interactions with current state of Discord API
        self.discord_bot: discord.Bot = discord_bot or None

        # For sending message
        self.discord_context: discord.ApplicationContext = discord_context or None

        # Google GenAI client, for efficiency we can reuse the same client instance
        # Check if its a legitimate client SDK from google.genai
        # Otherwise we create a new one
        if client_name and type(getattr(discord_bot, client_name, None)) == google_genai.Client:
            if not discord_bot and not isinstance(discord_bot, discord.Bot):
                raise ValueError("client_name is provided but discord_bot is None and is not a valid discord.Bot instance")

            logging.info("Reusing existing Google GenAI client from discord.Bot subclass: %s", client_name)
            self.google_genai_client: google_genai.Client = getattr(discord_bot, client_name)
        else:
            logging.info("Creating new Google GenAI client instance for ChatSessionGoogle")
            self.google_genai_client: google_genai.Client = google_genai.Client(api_key=config.get_api_key("gemini"))

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

        # If system instructions is disabled
        if not self.model_props.enable_system_instruction:
            system_instructions = None

        # Format the prompt
        _prep_prompt = {
            "role": "user",
            "parts": []
        }

        # Check if we have an attachment
        if hasattr(self, "uploaded_files") and self.uploaded_files:
            # Add the attachment part to the prompt
            _prep_prompt["parts"].extend(self.uploaded_files)
        
        # Append the actual prompt
        _prep_prompt["parts"].append({
            "text": prompt,
        })

        # Add the prepared prompt to chat history
        chat_history.append(_prep_prompt)

        # Check for tools
        if self.model_props.enable_tools:
            await self.load_tools()
            self.model_params["tools"] = [{"function_declarations": self.tool_schema}]

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
        _merged_params.pop("system_instruction", None)
        _merged_params.pop("tools", None)

        # Remove others found in model_params
        for _keys in self.model_params.keys():
            if _keys in _merged_params:
                logging.info("Removing key from additional_params to avoid conflict: %s", _keys)
                _merged_params.pop(_keys, None)

        # Update with model defaults
        _merged_params.update(self.model_params)
        
        # Generate
        try:
            _response: google_genai_types.GenerateContentResponse = await self.google_genai_client.aio.models.generate_content(
                model=self.model_props.model_id,
                contents=chat_history,
                config={
                    "system_instruction": system_instructions or None,
                    **_merged_params
                }
            )
        except google_genai_errors.ClientError as e:
            # Attempt to clear all file URLs since they may be expired
            if "do not have permission" in e.message:
                logging.error("Uh oh something went wrong while generating content, files may be expired, clearing files and raising error: %s", e)
                for _chat_turns in chat_history:
                    for _part in _chat_turns["parts"]:
                        # Check if we have file_data key then we just set it as None and set the text to "Expired"
                        if _part.get("file_data"):
                            _part["file_data"] = None
                            _part["text"] = "[<system_notice>File attachment processed but expired from history. DO NOT make stuff up about it! Ask the user to reattach for more details</system_notice>]"

                # Send message
                await self.discord_context.channel.send("Something went wrong, please send me a message again.")
                return chat_history
            else:
                logging.error("Uh oh something went wrong while generating content: %s", e)
                raise e

        # TODO: Add validation if the file expires from server
        # Either throw exception, reinit chat thread and throw exception, or rerun response with reinit chat thread

        # Check if the model reaches to STOP
        if not hasattr(_response, "candidates") and _response.candidates[0].finish_reason != "STOP":
            logging.warning("The model did not finish with STOP, it finished with: %s", _response.candidates[0].finish_reason)
            raise CustomErrorMessage("⚠️ The model did not return a response, please try again.")

        # Send each part of the response
        while True:
            _tool_parts = None
            # Iterate through each part of the response
            for _part in _response.candidates[0].content.parts:
                # Send text message if needed
                if _part.text and _part.text.strip():
                    await models.core.send_ai_response(self.discord_context, prompt, _part.text, self.discord_context.channel.send)

                # Render the code execution inline data when needed
                if _part.inline_data:
                    if _part.inline_data.mime_type == "image/png":
                        await self.discord_context.channel.send(file=discord.File(io.BytesIO(_part.inline_data.data), filename="image.png"))
                    elif _part.inline_data.mime_type == "image/jpeg":
                        await self.discord_context.channel.send(file=discord.File(io.BytesIO(_part.inline_data.data), filename="image.jpeg"))
                    else:
                        await self.discord_context.channel.send(file=discord.File(io.BytesIO(_part.inline_data.data), filename="code_exec_artifact.bin"))

                # Check for tool calls
                if _part.function_call:
                    chat_history.append(_response.candidates[0].content.model_dump(exclude_unset=True))

                    # Tool parts
                    _tool_parts = await self.execute_tools(name=_part.function_call.name, arguments=_part.function_call.args)

                    # Extend chat history with tool parts
                    chat_history.extend(_tool_parts)

                    # Run the response the second time
                    _response: google_genai_types.GenerateContentResponse = await self.google_genai_client.aio.models.generate_content(
                        model=self.model_props.model_id,
                        contents=chat_history,
                        config={
                            **self.model_params,
                            "system_instruction": system_instructions or None
                        }
                    )

            # Check if we need to run tools again, this block will stop the loop and response should have been sent
            # _tool_parts would indicate if we ran tools before, which means there is a new _response assigned
            if _tool_parts:
                if not _response.function_calls:
                    _textResponse = _response.text or _response.candidates[0].content.parts[-1].text
                    if _textResponse and _textResponse.strip():
                        await models.core.send_ai_response(self.discord_context, prompt, _textResponse, self.discord_context.channel.send)
                else:
                    continue  # Continue the while loop to process tool calls
                
            # Assuming everything went well
            break


        # Append to chat history
        chat_history.append(_response.candidates[0].content.model_dump(exclude_unset=True))
        # Return the chat history
        return chat_history