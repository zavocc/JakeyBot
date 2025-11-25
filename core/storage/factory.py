from .base import StorageProvider, StorageError
from typing import Dict, Type, Optional, Any
import logging

# Registry of available storage providers
_storage_providers: Dict[str, Type[StorageProvider]] = {}

logger = logging.getLogger(__name__)


def register_storage_provider(name: str, provider_class: Type[StorageProvider]) -> None:
    """
    Register a storage provider class.
    
    This allows for dynamic registration of custom storage providers
    without modifying the core codebase.
    
    Args:
        name: Unique identifier for the provider (e.g., "azure_blob", "s3", "gcp").
        provider_class: The StorageProvider subclass to register.
    
    Example:
        from core.storage import register_storage_provider, StorageProvider
        
        class MyCustomProvider(StorageProvider):
            async def upload(self, file_path, file_name, **kwargs):
                ...
            async def delete(self, file_identifier, **kwargs):
                ...
        
        register_storage_provider("my_custom", MyCustomProvider)
    """
    if not issubclass(provider_class, StorageProvider):
        raise TypeError(f"{provider_class} must be a subclass of StorageProvider")
    
    _storage_providers[name] = provider_class
    logger.info("Registered storage provider: %s", name)


def get_storage_provider(
    name: str,
    client: Optional[Any] = None,
    **config
) -> StorageProvider:
    """
    Get an instance of a registered storage provider.
    
    Args:
        name: The provider name (e.g., "azure_blob", "s3", "gcp").
        client: Optional pre-initialized client to pass to the provider.
        **config: Additional configuration options for the provider.
    
    Returns:
        StorageProvider: An instance of the requested provider.
    
    Raises:
        ValueError: If the provider name is not registered.
    
    Example:
        # Get Azure Blob provider with existing client
        provider = get_storage_provider(
            "azure_blob",
            client=bot.blob_service_client,
            container_name="my-container"
        )
        
        # Get S3 provider (if registered)
        provider = get_storage_provider(
            "s3",
            bucket_name="my-bucket",
            region="us-east-1"
        )
    """
    if name not in _storage_providers:
        available = list(_storage_providers.keys())
        raise ValueError(
            f"Unknown storage provider: {name}. "
            f"Available providers: {available}"
        )
    
    provider_class = _storage_providers[name]
    return provider_class(client=client, **config)


def list_storage_providers() -> list:
    """
    List all registered storage provider names.
    
    Returns:
        list: Names of all registered providers.
    """
    return list(_storage_providers.keys())


# Auto-register built-in providers
def _register_builtin_providers():
    """Register the built-in storage providers."""
    try:
        from .azure_blob import AzureBlobStorageProvider
        register_storage_provider("azure_blob", AzureBlobStorageProvider)
    except ImportError as e:
        logger.warning("Could not register Azure Blob provider: %s", e)


# Register built-in providers on module load
_register_builtin_providers()
