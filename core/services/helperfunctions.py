from azure.storage.blob.aio import BlobServiceClient
from os import environ
import aiofiles
import aiofiles.ospath
import discord
import yaml

class HelperFunctions:
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


