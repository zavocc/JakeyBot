from plugins.abc.storage import Storage, StorageOneOff
from plugins.validation import PluginsConfig
from pydantic import ValidationError
from typing import Union
import importlib
import yaml

class StoragePluginLoader:
    def __init__(self):
        # Read and validate plugin config.
        with open("plugins/config.yaml", "r") as f:
            self._loaded_config = yaml.safe_load(f) or {}

        try:
            _validated_config = PluginsConfig(**self._loaded_config)
            self.storage_config = _validated_config.storage
        except ValidationError as e:
            raise ValueError(f"Storage configuration validation failed: {e}") from e
        
        _storage_name = self.storage_config.name
        self._imported_module = importlib.import_module(f"plugins.storage.{_storage_name}")

        # Check if imported module have StoragePlugin class
        if not hasattr(self._imported_module, "StoragePlugin"):
            raise AttributeError(f"The storage plugin module 'plugins.storage.{_storage_name}' does not have a 'StoragePlugin' class.")

        self._storagepluginobject: Union[Storage, StorageOneOff] = self._imported_module.StoragePlugin()

        # Expose storage enabled flag from validated config.
        self.enabled = self.storage_config.enabled

        if isinstance(self._storagepluginobject, Storage):
            self.start_storage_client = self._storagepluginobject.start_storage_client
            self.close_storage_client = self._storagepluginobject.close_storage_client
            self.upload_files = self._storagepluginobject.upload_files
        elif isinstance(self._storagepluginobject, StorageOneOff):
            self.upload_files = self._storagepluginobject.upload_files
        else:
            raise TypeError("The storage plugin must implement either Storage or StorageOneOff interface.")