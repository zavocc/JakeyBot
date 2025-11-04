from .validation import ModelProps
from core.database import History
from core.exceptions import CustomErrorMessage
from os import environ
from pathlib import Path
from uuid import uuid4
import aiofiles
import logging
import mimetypes
import yaml

try:
    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob import ContentSettings
    from azure.storage.blob.aio import BlobServiceClient
except ImportError:  # pragma: no cover - handled at runtime if dependency missing
    ResourceExistsError = None
    ContentSettings = None
    BlobServiceClient = None
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


async def upload_blob_storage(path: str, data: bytes) -> str:
    """Upload a file buffer to the configured blob storage and return its public URL."""
    if BlobServiceClient is None or ContentSettings is None:
        logging.error("azure-storage-blob is not installed; blob uploads are unavailable")
        raise CustomErrorMessage("⚠️ File uploads are currently unavailable, please contact the administrator.")

    connection_string = environ.get("BLOB_STORAGE_CONNECTION_STRING")
    container_name = environ.get("BLOB_STORAGE_CONTAINER_NAME")

    if not connection_string or not container_name:
        logging.error("Blob storage configuration is missing environment variables")
        raise CustomErrorMessage("⚠️ File uploads are currently unavailable, please try again later.")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_name = Path(path).name or f"jakey_upload_{uuid4().hex}"
    blob_name = f"{uuid4().hex}_{blob_name}"

    guessed_content_type, _ = mimetypes.guess_type(blob_name)
    content_type = guessed_content_type or "application/octet-stream"

    try:
        container_client = blob_service_client.get_container_client(container_name)

        if ResourceExistsError is not None:
            try:
                await container_client.create_container()
            except ResourceExistsError:
                pass

        await container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )

        return f"{container_client.url}/{blob_name}"
    except Exception as exc:
        logging.exception("Failed to upload file to blob storage")
        raise CustomErrorMessage("⚠️ An error has occurred while uploading the file, please try again later.") from exc
    finally:
        await blob_service_client.close()
