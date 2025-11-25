from .base import StorageProvider, StorageUploadError, StorageDeleteError, StorageNotFoundError
from azure.storage.blob.aio import BlobServiceClient
from os import environ
from pathlib import Path
from typing import Optional, Union
import aiofiles

class AzureBlobStorageProvider(StorageProvider):
    """
    Azure Blob Storage implementation of StorageProvider.
    
    This provider supports uploading, deleting, and managing files
    in Azure Blob Storage containers.
    
    Example usage:
        # With existing client (recommended for bot integration)
        provider = AzureBlobStorageProvider(
            client=bot.blob_service_client,
            container_name="my-container"
        )
        
        # Or create its own client
        provider = AzureBlobStorageProvider(
            connection_string="...",
            container_name="my-container"
        )
        
        url = await provider.upload("/path/to/file.png", "file.png")
    """
    
    def __init__(
        self,
        client: Optional[BlobServiceClient] = None,
        connection_string: Optional[str] = None,
        container_name: Optional[str] = None,
        **config
    ):
        """
        Initialize Azure Blob Storage provider.
        
        Args:
            client: Optional pre-initialized BlobServiceClient.
            connection_string: Azure Storage connection string (used if client not provided).
                             Defaults to AZURE_STORAGE_CONNECTION_STRING env var.
            container_name: Name of the blob container to use.
                          Defaults to AZURE_STORAGE_CONTAINER_NAME env var.
            **config: Additional configuration options.
        """
        super().__init__(client=client, **config)
        
        self.connection_string = connection_string or environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = container_name or environ.get("AZURE_STORAGE_CONTAINER_NAME")
        
        if not self.container_name:
            raise ValueError("container_name must be provided or set via AZURE_STORAGE_CONTAINER_NAME env var")
    
    async def _get_client(self) -> BlobServiceClient:
        """Get or create the blob service client."""
        if self.client is not None:
            return self.client
        
        if not self.connection_string:
            raise ValueError("connection_string must be provided or set via AZURE_STORAGE_CONNECTION_STRING env var")
        
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        self._owns_client = True
        return self.client
    
    async def upload(
        self,
        file_path: Union[str, Path],
        file_name: str,
        overwrite: bool = False,
        content_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Local path to the file to upload.
            file_name: Name to use for the blob.
            overwrite: Whether to overwrite existing blobs. Defaults to False.
            content_type: Optional MIME type for the blob.
            **kwargs: Additional options passed to upload_blob().
        
        Returns:
            str: Public URL of the uploaded blob.
        
        Raises:
            StorageUploadError: If the upload fails.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise StorageUploadError(f"File not found: {file_path}")
        
        try:
            client = await self._get_client()
            blob_client = client.get_blob_client(
                container=self.container_name,
                blob=file_name
            )
            
            async with aiofiles.open(file_path, "rb") as file_data:
                content = await file_data.read()
                await blob_client.upload_blob(
                    content,
                    overwrite=overwrite,
                    content_type=content_type,
                    **kwargs
                )
            
            self.logger.info("Successfully uploaded %s to Azure Blob Storage", file_name)
            return blob_client.url
            
        except Exception as e:
            self.logger.error("Error uploading file %s to blob storage: %s", file_name, e)
            raise StorageUploadError(f"Failed to upload {file_name}: {e}") from e
    
    async def upload_from_bytes(
        self,
        data: bytes,
        file_name: str,
        overwrite: bool = False,
        content_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Upload file content directly from bytes to Azure Blob Storage.
        
        Args:
            data: The file content as bytes.
            file_name: Name to use for the blob.
            overwrite: Whether to overwrite existing blobs.
            content_type: Optional MIME type for the blob.
            **kwargs: Additional options.
        
        Returns:
            str: Public URL of the uploaded blob.
        """
        try:
            client = await self._get_client()
            blob_client = client.get_blob_client(
                container=self.container_name,
                blob=file_name
            )
            
            await blob_client.upload_blob(
                data,
                overwrite=overwrite,
                content_type=content_type,
                **kwargs
            )
            
            self.logger.info("Successfully uploaded %s to Azure Blob Storage from bytes", file_name)
            return blob_client.url
            
        except Exception as e:
            self.logger.error("Error uploading bytes to blob storage as %s: %s", file_name, e)
            raise StorageUploadError(f"Failed to upload {file_name}: {e}") from e
    
    async def delete(self, file_identifier: str, **kwargs) -> bool:
        """
        Delete a blob from Azure Blob Storage.
        
        Args:
            file_identifier: The blob name or URL to delete.
            **kwargs: Additional options passed to delete_blob().
        
        Returns:
            bool: True if deletion was successful.
        
        Raises:
            StorageDeleteError: If the deletion fails.
        """
        # Extract blob name from URL if necessary
        blob_name = self._extract_blob_name(file_identifier)
        
        try:
            client = await self._get_client()
            blob_client = client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await blob_client.delete_blob(**kwargs)
            self.logger.info("Successfully deleted blob %s", blob_name)
            return True
            
        except Exception as e:
            self.logger.error("Error deleting blob %s: %s", blob_name, e)
            raise StorageDeleteError(f"Failed to delete {blob_name}: {e}") from e
    
    async def exists(self, file_identifier: str, **kwargs) -> bool:
        """
        Check if a blob exists in Azure Blob Storage.
        
        Args:
            file_identifier: The blob name or URL to check.
            **kwargs: Additional options.
        
        Returns:
            bool: True if the blob exists.
        """
        blob_name = self._extract_blob_name(file_identifier)
        
        try:
            client = await self._get_client()
            blob_client = client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            return await blob_client.exists()
            
        except Exception as e:
            self.logger.error("Error checking blob existence for %s: %s", blob_name, e)
            return False
    
    async def get_url(self, file_identifier: str, **kwargs) -> str:
        """
        Get the URL for a blob.
        
        Args:
            file_identifier: The blob name.
            **kwargs: Additional options (e.g., for SAS token generation).
        
        Returns:
            str: The blob URL.
        """
        blob_name = self._extract_blob_name(file_identifier)
        
        client = await self._get_client()
        blob_client = client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        return blob_client.url
    
    def _extract_blob_name(self, file_identifier: str) -> str:
        """
        Extract blob name from a URL or return as-is if already a name.
        
        Args:
            file_identifier: URL or blob name.
        
        Returns:
            str: The blob name.
        """
        # If it looks like a URL, extract the blob name
        if file_identifier.startswith("http"):
            # URL format: https://<account>.blob.core.windows.net/<container>/<blob_name>
            parts = file_identifier.split(f"/{self.container_name}/")
            if len(parts) > 1:
                return parts[1].split("?")[0]  # Remove any query params
        return file_identifier
    
    async def close(self) -> None:
        """Close the blob service client if we own it."""
        if self._owns_client and self.client is not None:
            self.logger.info("Closing owned BlobServiceClient instance")
            await self.client.close()
            self.client = None
