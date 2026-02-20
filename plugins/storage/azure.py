from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from core.exceptions import CustomErrorMessage
from core.abc import StoragePlugin
from os import environ
import aiofiles
import filetype
import logging

class Plugin(StoragePlugin):
    async def upload_file(self, file_path: str, file_name: str, client: BlobServiceClient = None) -> str:
        # Check if we have a blob service client
        if not client:
            _blob_service_client = BlobServiceClient.from_connection_string(environ.get("AZURE_STORAGE_CONNECTION_STRING"))
        else:
            _blob_service_client = client

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
            if not client:
                logging.info("Closing one-off BlobServiceClient instance.")
                await _blob_service_client.close()
