from .validation import ModelProps
from azure.storage.blob.aio import BlobServiceClient
from core.database import History
from core.exceptions import CustomErrorMessage
from core.storage import get_storage_provider, StorageProvider, StorageUploadError
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

# Upload files to storage (modular approach)
async def upload_files_to_storage(
    file_path: str,
    file_name: str,
    storage_provider: StorageProvider = None,
    **kwargs
) -> str:
    """
    Upload a file using a storage provider.
    
    This is the recommended way to upload files, supporting any registered
    storage provider (Azure Blob, S3, GCP, etc.).
    
    Args:
        file_path: Local path to the file to upload.
        file_name: Name to use for the uploaded file.
        storage_provider: A StorageProvider instance. If not provided,
                         creates a default Azure Blob provider.
        **kwargs: Additional options passed to the provider's upload method.
    
    Returns:
        str: Public URL or identifier for the uploaded file.
    
    Example:
        # With existing provider from bot
        url = await upload_files_to_storage(
            "/path/to/file.png",
            "file.png",
            storage_provider=bot.storage_provider
        )
        
        # Or create one-off provider
        provider = get_storage_provider("azure_blob", client=blob_client)
        async with provider:
            url = await upload_files_to_storage("/path/to/file.png", "file.png", provider)
    """
    _owns_provider = False
    
    try:
        if storage_provider is None:
            # Create default Azure Blob provider for backward compatibility
            storage_provider = get_storage_provider("azure_blob")
            _owns_provider = True
        
        return await storage_provider.upload(file_path, file_name, **kwargs)
    
    except StorageUploadError as e:
        logging.error("Storage upload error for %s: %s", file_name, e)
        raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")
    except Exception as e:
        logging.error("Unexpected error uploading file %s: %s", file_name, e)
        raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")
    finally:
        if _owns_provider and storage_provider is not None:
            await storage_provider.close()

# Upload files to blob storage (legacy - kept for backward compatibility)
async def upload_files_blob(file_path: str, file_name: str, blob_service_client: BlobServiceClient = None):
    """
    Upload a file to Azure Blob Storage.
    
    DEPRECATED: Use upload_files_to_storage() with a StorageProvider for new code.
    This function is kept for backward compatibility.
    
    Args:
        file_path: Local path to the file to upload.
        file_name: Name to use for the blob.
        blob_service_client: Optional BlobServiceClient. If not provided,
                           creates one from AZURE_STORAGE_CONNECTION_STRING.
    
    Returns:
        str: Public URL of the uploaded blob.
    """
    logging.warning(
        "upload_files_blob is deprecated. Use upload_files_to_storage with StorageProvider instead."
    )
    
    # Use the new modular system under the hood
    storage_provider = get_storage_provider(
        "azure_blob",
        client=blob_service_client
    )
    
    try:
        return await storage_provider.upload(file_path, file_name, overwrite=False)
    except StorageUploadError:
        raise CustomErrorMessage("⚠️ There was an error uploading your file, please try again later.")
    finally:
        # Only close if we didn't receive an external client
        if blob_service_client is None:
            await storage_provider.close()
    