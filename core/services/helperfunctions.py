from azure.storage.blob.aio import BlobServiceClient
from os import environ
from typing import Literal
from typing import TypedDict
import aiofiles
import aiofiles.ospath
import discord
import logging
import yaml

class DefaultModelDict(TypedDict):
    provider: Literal["gemini"]
    model_name: str

# You can choose other service like GCP or your custom solution
class HelperFunctions:
    # Default model getter
    # TODO: When adding multiple models, we may need to use YAML-based or environment-based configuration
    # Right now Gemini is the solid choice for almost everything. 
    # Also, prevent breaking changes... we keep the same structure
    @staticmethod
    def fetch_default_model(
        model_type: Literal["base", "reasoning"] = "base",
        output_modalities: Literal["text", "image"] = "text",
        provider: Literal["gemini"] = "gemini"
    ) -> DefaultModelDict:
        # Check if the model type is valid
        if not any(output_modalities == _types for _types in ["text", "image"]):
            raise ValueError("Invalid model type. Must be 'text' or 'image'")
        # Check if the provider is valid
        if not any(provider == _provider for _provider in ["gemini"]):
            raise ValueError("Invalid provider. Only supported ones is 'gemini'")
        
        # Constructed dict
        _constructed_dict = {
            "provider": provider,
        }

        # Return the default model based on the type and provider
        if provider == "gemini":
            if output_modalities == "text":
                if model_type == "base":
                    _constructed_dict["model_name"] = "gemini-2.5-flash-nonthinking"
                elif model_type == "reasoning":
                    _constructed_dict["model_name"] = "gemini-2.5-flash"
            elif output_modalities == "image":
                if model_type == "base":
                    _constructed_dict["model_name"] = "gemini-2.0-flash-preview-image-generation"
                elif model_type == "reasoning":
                    raise ValueError("Reasoning mode is not supported for image output modality")
        else:
            raise ValueError("Unsupported provider. Only 'gemini' is supported")
        
        # Log for debugging
        logging.info("Fetched and used default model | Provider: %s | Model: %s | Type: %s | Output Modality: %s |  ", 
            provider,
            _constructed_dict["model_name"],
            model_type,
            output_modalities
        )        
        return _constructed_dict

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
        # We format {} to have emojis, if we use type 0
        if type == 0 and (await aiofiles.ospath.exists("emojis.yaml")):
            # The yaml format is
            # - emoji1
            # - emoji2
            # So we need to join them with newline and dash each same as yaml 
            async with aiofiles.open("emojis.yaml") as emojis_list:
                _emojis_list = "\n - ".join(yaml.safe_load(await emojis_list.read()))
                print(_emojis_list)

                if not _emojis_list:
                    _emojis_list = "No emojis found"
            return _assistants_mode[assistant_name].strip().format(_emojis_list)
        else:
            return _assistants_mode[assistant_name].strip()


