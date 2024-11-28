import aiofiles
import aiohttp
import logging

############################
# File upload
############################
async def hm_chunker(file_path, chunk_size=8192):
    async with aiofiles.open(file_path, "rb") as _file:
        _chunk = await _file.read(chunk_size)
        while _chunk:
            yield _chunk
            _chunk = await _file.read(chunk_size)

############################
# Raise for status wrapper
# For logging and error handling
############################
async def hm_raise_for_status(response: aiohttp.ClientResponse):
    try:
        response.raise_for_status()
    except aiohttp.ClientResponseError as e:
        logging.error("%s: I think I found a problem related to the request: %s", (await aiofiles.ospath.abspath(__file__)), e)
        raise e
    