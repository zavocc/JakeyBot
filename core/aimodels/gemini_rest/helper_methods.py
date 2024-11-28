from core.exceptions import GeminiClientRequestError
import aiofiles
import aiohttp

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
    except aiohttp.ClientResponseError:
        if response.headers.get("Content-Type") == "application/json":
            raise GeminiClientRequestError(error_code=(await response.json())["error"]["code"], 
                                            error_message=(await response.json())["error"]["message"])
        else:
            raise GeminiClientRequestError(error_code=response.status, error_message=response.reason)