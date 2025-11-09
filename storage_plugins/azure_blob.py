from __future__ import annotations

import logging
from os import environ
import importlib
from typing import Any, Optional

import aiofiles

from .base import StoragePlugin


class AzureBlobStoragePlugin(StoragePlugin):
    """Storage plugin backed by Azure Blob Storage."""

    name = "azure_blob"

    def __init__(self, options: Optional[dict] = None):
        super().__init__(options)
        self._container_name: Optional[str] = None
        self._blob_client_cls = None

    async def setup(self) -> None:
        try:
            _azure_blob_module = importlib.import_module("azure.storage.blob.aio")
            BlobServiceClient = getattr(_azure_blob_module, "BlobServiceClient")
        except ImportError as _exc:
            raise RuntimeError(
                "azure-storage-blob is required to use AzureBlobStoragePlugin. "
                "Install it or choose another storage plugin."
            ) from _exc
        except AttributeError as _exc:
            raise RuntimeError("BlobServiceClient not found in azure.storage.blob.aio module.") from _exc

        _connection_string_env = self.options.get("connection_string_env", "AZURE_STORAGE_CONNECTION_STRING")
        _container_env = self.options.get("container_env", "AZURE_STORAGE_CONTAINER_NAME")

        _connection_string = environ.get(_connection_string_env)
        if not _connection_string:
            raise RuntimeError(f"Missing {_connection_string_env} environment variable for Azure storage plugin.")

        _container_name = environ.get(_container_env)
        if not _container_name:
            raise RuntimeError(f"Missing {_container_env} environment variable for Azure storage plugin.")

        self._container_name = _container_name
        self._blob_client_cls = BlobServiceClient
        self.client = BlobServiceClient.from_connection_string(_connection_string)
        logging.info("AzureBlobStoragePlugin initialized for container %s", _container_name)

    async def teardown(self) -> None:
        if self.client:
            await self.client.close()
            logging.info("AzureBlobStoragePlugin client closed successfully.")

    async def upload(self, file_path: str, file_name: str, client: Any = None) -> str:
        if not self._container_name:
            raise RuntimeError("AzureBlobStoragePlugin is not configured with a container name.")

        _client = client or self.client
        if _client is None:
            raise RuntimeError("AzureBlobStoragePlugin requires a BlobServiceClient instance.")

        _blob_client = _client.get_blob_client(container=self._container_name, blob=file_name)

        async with aiofiles.open(file_path, "rb") as _file_handle:
            await _blob_client.upload_blob(_file_handle, overwrite=self.options.get("overwrite", False))

        logging.info("Uploaded %s to Azure blob container %s", file_name, self._container_name)
        return _blob_client.url
