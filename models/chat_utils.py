from .validation import ModelProps
from azure.storage.blob.aio import BlobServiceClient
from core.database import History
from core.exceptions import CustomErrorMessage
from os import environ
import aiofiles
import filetype
import logging
import yaml
# Methods for generative_chat.py

# Fetch and validate models
async def fetch_model(model_alias: str) -> ModelProps:
    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(await models.read())

    # Find the model dict with the matching alias
    _model_dict = next((mdl for mdl in _models_list if mdl.get("model_alias") == model_alias), None)

    if not _model_dict:
        raise CustomErrorMessage("⚠️ The current model you had chosen is not yet available, please try another model.")

    return ModelProps(**_model_dict)

# Load chat history from thread_name
async def load_history(user_id: int, thread_name: str, db_conn: History) -> list:
    """Fetch chat history for a specific thread_name using get_key method."""
    try:
        _history = await db_conn.get_key(user_id, f"chat_thread_{thread_name}")
        return _history # Returns none for new threads
    except Exception as e:
        logging.error("Error loading history for thread_name %s, reason: %s", thread_name, e)
        return None

# Save chat history
async def save_history(user_id: int, thread_name: str, chat_thread: list, db_conn: History) -> None:
    """Save chat history for a specific thread_name using set_key method."""
    await db_conn.set_key(user_id, f"chat_thread_{thread_name}", chat_thread)

# Upload files to blob storage
async def upload_files_blob(file_path: str, file_name: str, blob_service_client: BlobServiceClient = None):
    # Check if we have a blob service client
    if not blob_service_client:
        _blob_service_client = BlobServiceClient.from_connection_string(environ.get("AZURE_STORAGE_CONNECTION_STRING"))
    else:
        _blob_service_client = blob_service_client

    # Upload the file
    try:
        _blob_client = _blob_service_client.get_blob_client(container=environ.get("AZURE_STORAGE_CONTAINER_NAME"), blob=file_name)

        async with aiofiles.open(file_path, "rb") as _file_data:
            await _blob_client.upload_blob(_file_data, overwrite=False)

        # Return the blob URL
        return _blob_client.url
    except Exception as e:
        logging.error("Error uploading file %s to blob storage, reason: %s", file_name, e)
        raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")
    finally:
        if not blob_service_client:
            logging.info("Closing one-off BlobServiceClient instance.")
            await _blob_service_client.close()
    