from core.exceptions import GeminiClientRequestError
import logging
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
    except aiohttp.ClientResponseError as e:
        logging.error("I think I found a problem related to the request: %s", e)
        # Usually in some cases, the response body is in JSON format, and sometimes its text/plain or text/html
        # So check the content type and raise the error accordingly
        if response.headers.get("Content-Type") == "application/json":
            _json_response = await response.json()
            raise GeminiClientRequestError(
                message=_json_response["error"]["message"],
                error_code=_json_response["error"]["code"] 
            )
        else:
            raise GeminiClientRequestError(message=response.reason or "Request Failed", error_code=response.status)