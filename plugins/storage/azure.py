from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from core.exceptions import CustomErrorMessage
from os import environ
from plugins.abc.storage import Storage
import aiofiles
import filetype
import logging

class StoragePlugin(Storage):
    def __init__(self):
        self.blob_service_client = None

    def start_storage_client(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            conn_str=environ.get("AZURE_STORAGE_CONNECTION_STRING"),
            max_block_size=8*1024*1024,  # 8 MB chunk size
            max_single_put_size=8*1024*1024
        )
        logging.info("Blob service client initialized successfully")

    async def upload_files(self, file_path: str, file_name: str) -> str:
        # Check if we have a blob service client
        if not self.blob_service_client:
            _blob_service_client = BlobServiceClient.from_connection_string(environ.get("AZURE_STORAGE_CONNECTION_STRING"))
        else:
            _blob_service_client = self.blob_service_client

        # Upload the file
        try:
            _blob_client = _blob_service_client.get_blob_client(container=environ.get("AZURE_STORAGE_CONTAINER_NAME"), blob=file_name)

            async with aiofiles.open(file_path, "rb") as _file_data:
                _file_bytes = await _file_data.read()
                _mime_type = filetype.guess(_file_bytes)
                await _blob_client.upload_blob(_file_bytes, 
                                            overwrite=False,
                                            content_settings=ContentSettings(content_type=_mime_type.mime if _mime_type else "application/octet-stream"))

            # Return the blob URL
            return _blob_client.url
        except Exception as e:
            logging.error("Error uploading file %s to blob storage, reason: %s", file_name, e)
            raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")
        finally:
            if not self.blob_service_client:
                logging.info("Closing one-off BlobServiceClient instance.")
                await _blob_service_client.close()

    async def close_storage_client(self):
        # Close blob service client sessions if any
        if hasattr(self, 'blob_service_client'):
            await self.blob_service_client.close()
            logging.info("Blob service client session closed successfully")