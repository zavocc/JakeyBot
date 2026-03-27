from abc import ABC, abstractmethod

# Storage ABC without client object.
class StorageOneOff(ABC):
    @abstractmethod
    async def upload_files(file_path: str, file_name: str):
        pass

class Storage(ABC):
    @abstractmethod
    def start_storage_client(self):
        pass

    @abstractmethod
    async def upload_files(file_path: str, file_name: str) -> str:
        pass

    @abstractmethod
    async def close_storage_client(self):
        pass