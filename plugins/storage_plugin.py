from plugins.abc.storage import Storage, StorageOneOff
from typing import Union
import importlib
import yaml

class StoragePluginLoader:
    def __init__(self):
        # Read YAML see if it has "storage" key with "name" key inside
        with open("plugins/config.yaml", "r") as f:
            self._loaded_config = yaml.safe_load(f)

            # check if None
            if self._loaded_config is None:
                raise ValueError("Config file is empty or invalid YAML format.")
        
        # Check if storage config is valid
        if not self._loaded_config.get("storage") or not self._loaded_config.get("storage").get("name"):
            raise ValueError("Storage configuration is missing or invalid in config.yaml")
        
        _storage_name = self._loaded_config["storage"]["name"].lower()
        self._imported_module = importlib.import_module(f"plugins.storage.{_storage_name}")

        # Check if imported module have StoragePlugin class
        if not hasattr(self._imported_module, "StoragePlugin"):
            raise AttributeError(f"The storage plugin module 'plugins.storage.{_storage_name}' does not have a 'StoragePlugin' class.")

        self._storagepluginobject: Union[Storage, StorageOneOff] = self._imported_module.StoragePlugin()

        if isinstance(self._storagepluginobject, Storage):
            self.start_storage_client = self._storagepluginobject.start_storage_client
            self.close_storage_client = self._storagepluginobject.close_storage_client
            self.upload_files = self._storagepluginobject.upload_files
        elif isinstance(self._storagepluginobject, StorageOneOff):
            self.upload_files = self._storagepluginobject.upload_files
        else:
            raise TypeError("The storage plugin must implement either Storage or StorageOneOff interface.")
   