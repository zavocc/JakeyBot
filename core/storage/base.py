from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Union
from pathlib import Path
import logging


class StorageProvider(ABC):
    """
    Abstract base class for file storage providers.
    
    All storage implementations must inherit from this class and implement
    the required methods. This ensures a consistent interface across different
    storage backends (Azure Blob, S3, GCP, Discord CDN, local file server, etc.)
    
    Example usage:
        class MyStorageProvider(StorageProvider):
            async def upload(self, file_path, file_name, **kwargs):
                # Implementation
                return "https://example.com/file.png"
            
            async def delete(self, file_identifier, **kwargs):
                # Implementation
                return True
    """
    
    def __init__(self, client: Optional[object] = None, **config):
        """
        Initialize the storage provider.
        
        Args:
            client: Optional pre-initialized client instance (e.g., BlobServiceClient, S3Client)
                   If not provided, the provider should create its own client.
            **config: Additional configuration options specific to the provider.
        """
        self.client = client
        self.config = config
        self._owns_client = client is None  # Track if we created the client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def upload(
        self,
        file_path: Union[str, Path],
        file_name: str,
        **kwargs
    ) -> str:
        """
        Upload a file to the storage backend.
        
        Args:
            file_path: Local path to the file to upload.
            file_name: Name to use for the uploaded file in storage.
            **kwargs: Additional provider-specific options (e.g., content_type, metadata).
        
        Returns:
            str: Public URL or identifier for the uploaded file.
        
        Raises:
            StorageUploadError: If the upload fails.
        """
        pass
    
    @abstractmethod
    async def delete(self, file_identifier: str, **kwargs) -> bool:
        """
        Delete a file from the storage backend.
        
        Args:
            file_identifier: The URL, blob name, or identifier of the file to delete.
            **kwargs: Additional provider-specific options.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        
        Raises:
            StorageDeleteError: If the deletion fails.
        """
        pass
    
    async def exists(self, file_identifier: str, **kwargs) -> bool:
        """
        Check if a file exists in the storage backend.
        
        Args:
            file_identifier: The URL, blob name, or identifier of the file.
            **kwargs: Additional provider-specific options.
        
        Returns:
            bool: True if the file exists, False otherwise.
        
        Note:
            This method has a default implementation that returns True.
            Override this method for providers that support existence checks.
        """
        self.logger.warning(
            "exists() not implemented for %s, returning True by default",
            self.__class__.__name__
        )
        return True
    
    async def get_url(self, file_identifier: str, **kwargs) -> str:
        """
        Get the public URL for a file.
        
        Args:
            file_identifier: The blob name or identifier of the file.
            **kwargs: Additional provider-specific options (e.g., expiry for signed URLs).
        
        Returns:
            str: Public or signed URL for the file.
        
        Note:
            This method has a default implementation that returns the identifier.
            Override for providers that need URL generation.
        """
        return file_identifier
    
    async def upload_from_bytes(
        self,
        data: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Upload file content directly from bytes.
        
        Args:
            data: The file content as bytes.
            file_name: Name to use for the uploaded file.
            content_type: Optional MIME type of the file.
            **kwargs: Additional provider-specific options.
        
        Returns:
            str: Public URL or identifier for the uploaded file.
        
        Note:
            Default implementation writes to a temp file and calls upload().
            Override for more efficient implementations.
        """
        import aiofiles
        import tempfile
        import os
        
        # Default implementation: write to temp file and upload
        temp_path = Path(tempfile.gettempdir()) / file_name
        try:
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(data)
            return await self.upload(temp_path, file_name, content_type=content_type, **kwargs)
        finally:
            if temp_path.exists():
                os.remove(temp_path)
    
    async def close(self) -> None:
        """
        Close and cleanup the storage provider's resources.
        
        Override this method to properly close client connections
        when the provider owns its client instance.
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()
        return False


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class StorageUploadError(StorageError):
    """Raised when a file upload fails."""
    pass


class StorageDeleteError(StorageError):
    """Raised when a file deletion fails."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when a file is not found."""
    pass
