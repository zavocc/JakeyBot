from .base import StorageProvider
from azure.storage.blob.aio import BlobServiceClient
from core.exceptions import CustomErrorMessage
import aiofiles
import logging

class AzureBlobStorage(StorageProvider):
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.service_client = None

    async def _get_client(self):
        if not self.service_client:
            self.service_client = BlobServiceClient.from_connection_string(self.connection_string)
        return self.service_client

    async def upload_file(self, file_path: str, file_name: str) -> str:
        client = await self._get_client()
        try:
            blob_client = client.get_blob_client(container=self.container_name, blob=file_name)
            
            async with aiofiles.open(file_path, "rb") as data:
                await blob_client.upload_blob(data, overwrite=False)
            
            return blob_client.url
        except Exception as e:
            logging.error(f"Error uploading file {file_name} to Azure Blob Storage: {e}")
            raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")

    async def close(self):
        if self.service_client:
            await self.service_client.close()
            logging.info("Azure Blob Storage client closed.")
