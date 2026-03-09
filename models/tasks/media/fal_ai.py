from os import environ
from typing import Any, Union
import aiohttp
import fal_client

# This method outputs bytes
async def run_image(
    model_name: str,
    aiohttp_session: aiohttp.ClientSession = None,
    send_bytes: bool = True,
    **additional_client_args
) -> dict[str, list[Any]]:
        # Check if we have aiohttp session supplied or use the default one
        if send_bytes:
            if not aiohttp_session:
                raise ValueError("aiohttp_session must be provided if send_bytes is True")
            _aiohttp_session = aiohttp_session
    
        # check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("FAL_KEY is not set! Cannot proceed generating images")
        
        # Construct params
        _params = {}
        _endpoint = f"fal-ai/{model_name}"

        # Additional client args
        if additional_client_args:
            _params.update(additional_client_args)

        # Generate an image
        _status = await fal_client.submit_async(
            _endpoint,
            arguments = _params
        )

        # Wait for the result
        _result = await _status.get()

        # Extract the image URLs.
        _images_urls = [_image["url"] for _image in _result["images"]]
        _response_payload: dict[str, list[Any]] = {
            "images_urls": _images_urls,
            "images_in_bytes": []
        }

        if send_bytes:
            # Image in bytes
            _images_in_bytes = []

            # Download images
            for _image_url in _images_urls:
                async with _aiohttp_session.get(_image_url) as response:
                    if response.status == 200:
                        _image_data = await response.read()
                    
                        # Send the image
                        _images_in_bytes.append(_image_data)
                    else:
                        raise ValueError(f"Failed to download image from {_image_url}, status code: {response.status}")

            _response_payload["images_in_bytes"] = _images_in_bytes

        # Cleanup
        return _response_payload

async def run_audio(
    model_name: str,
    aiohttp_session: aiohttp.ClientSession = None,
    send_url_only: bool = False,
    **additional_client_args
) -> Union[bytes, str]:
        # Check if we have aiohttp session supplied or use the default one
        if not send_url_only:
            if not aiohttp_session:
                raise ValueError("aiohttp_session must be provided if send_url_only is False")
            _aiohttp_session = aiohttp_session
    
        # check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("FAL_KEY is not set! Cannot proceed generating audios")
        
        # Construct params
        _params = {}
        _endpoint = f"fal-ai/{model_name}"

        # Additional client args
        if additional_client_args:
            _params.update(additional_client_args)

        # Generate an audio
        _status = await fal_client.submit_async(
            _endpoint,
            arguments = _params
        )

        # Wait for the result
        _result = await _status.get()

        # audio in bytes
        _audios_in_bytes = None

        if send_url_only:
            return _result["audio"]["url"]
        else:
            # Download audios
            async with _aiohttp_session.get(_result["audio"]["url"]) as response:
                if response.status == 200:
                    _audio_data = await response.read()
                    
                    # Send the audio
                    _audios_in_bytes = _audio_data
                else:
                    raise ValueError(f"Failed to download audio from {_result['audio']['url']}, status code: {response.status}")

            # Cleanup
            return _audios_in_bytes
        