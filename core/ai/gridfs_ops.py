import gridfs
import logging

class GridFSOps:
    def __init__(self, gridfs_bucket: gridfs.AsyncGridFSBucket):
        self._gridfs_bucket = gridfs_bucket

    async def upload_file(self, guild_id: int, model_provider: str, file_data):
        _filename = f"{guild_id}_{model_provider}.json"
        _file_id = await self._gridfs_bucket.upload_from_stream(_filename, file_data)
        logging.info(f"File uploaded with ID: {_file_id} with associated filename: {_filename}")
        return _file_id
    
    async def fetch_file(self, file_id):
        _file_data = await self._gridfs_bucket.open_download_stream(file_id)
        if _file_data is None:
            raise FileNotFoundError(f"File with ID {file_id} not found.")
        logging.info(f"File with ID {file_id} fetched successfully.")
        return await _file_data.read()

    async def delete_file(self, file_id):
        await self._gridfs_bucket.delete(file_id)
        logging.info(f"File with ID {file_id} deleted successfully.")
