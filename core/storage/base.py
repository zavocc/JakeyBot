from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    async def upload_file(self, file_path: str, file_name: str) -> str:
        """
        Uploads a file to the storage provider and returns the public URL.
        
        :param file_path: The absolute path to the file on the local disk.
        :param file_name: The name of the file to be stored.
        :return: The public URL of the uploaded file.
        """
        pass

    async def close(self):
        """Closes any underlying connections."""
        pass
