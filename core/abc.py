from abc import ABC, abstractmethod

class StoragePlugin(ABC):
    @abstractmethod
    async def upload_file(self, file_path: str, file_name: str, client=None) -> str:
        """Uploads a file and returns the URL as a string."""
        pass
