from azure.storage.blob.aio import BlobServiceClient
from os import environ
import discord

# You can choose other service like GCP or your custom solution
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

