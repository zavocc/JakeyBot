from azure.storage.blob.aio import BlobServiceClient
from os import environ
from typing import Literal
import aiofiles
import discord
import logging
import yaml

# You can choose other service like GCP or your custom solution
class HelperFunctions:
    # Default model getter
    @staticmethod
    def fetch_default_model(model_type: Literal["base_chat_model", "gemini_default_model", "gemini_image_generation"] = "base_chat_model") -> str:
        # Get the default envvars
        if model_type == "base_chat_model":
            _model = environ.get("DEFAULT_CHAT_MODEL", "google::gemini-2.5-flash")
            logging.info("Using default chat model: %s", _model)
            return _model
        elif model_type == "gemini_default_model":
            _model = environ.get("DEFAULT_GEMINI_MODEL", "gemini-2.5-flash")
            logging.info("Using default Gemini utility model: %s", _model)
            return _model
        elif model_type == "gemini_image_generation":
            _model = environ.get("DEFAULT_GEMINI_IMAGE_GENERATION_MODEL", "gemini-2.0-flash-preview-image-generation")
            logging.info("Using default gemini image generation model: %s", _model)
            return _model
        else:
            raise ValueError(f"Invalid model type: {model_type}. Must be one of 'base_chat_model', 'gemini_default_model', or 'image_generation'.")


    # Requires "bot" to access services
    @staticmethod
    async def upload_file_service(bot: discord.Bot, filename: str, data: bytes) -> None:
         # Get container client
        _service: BlobServiceClient = bot._azure_blob_service_client
        _container_client = _service.get_container_client(environ.get("AZURE_STORAGE_CONTAINER_NAME"))

        # Upload file to Azure Blob Storage
        await _container_client.upload_blob(
            name=filename,
            data=data,
            overwrite=True
        )

        # Return the URL of the uploaded file
        return f"{environ.get('AZURE_STORAGE_ACCOUNT_URL')}/{environ.get('AZURE_STORAGE_CONTAINER_NAME')}/{filename}"
            
    # Default assistants
    # function to get the assistants
    @staticmethod
    async def set_assistant_type(assistant_name: str, type: int = 0):
        # 0 - chat_assistants
        # 1 - utility_assistants

        # Load the assistants from YAML file
        async with aiofiles.open("data/assistants.yaml", "r") as assistants:
            _assistants_data = yaml.safe_load(await assistants.read())

        if type == 0:
            _assistants_mode = _assistants_data["chat_assistants"]
        else:
            _assistants_mode = _assistants_data["utility_assistants"]

        # Return the assistant
        return _assistants_mode[assistant_name].strip()


