from os import environ
from typing import Union
import aiohttp
import fal_client

# This method outputs bytes
async def run_image(
    model_name: str,
    aiohttp_session: aiohttp.ClientSession,
    send_url_only: bool = False,
    **additional_client_args
) -> list :
        # Check if we have aiohttp session supplied or use the default one
        if aiohttp_session:
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

        if send_url_only:
            return [_image["url"] for _image in _result["images"]]
        else:
            # Image in bytes
            _images_in_bytes = []

            # Download images
            for _images in _result["images"]:
                async with _aiohttp_session.get(_images["url"]) as response:
                    if response.status == 200:
                        _image_data = await response.read()
                    
                        # Send the image
                        _images_in_bytes.append(_image_data)
                    else:
                        raise ValueError(f"Failed to download image from {_images}, status code: {response.status}")

            # Cleanup
            return _images_in_bytes

async def run_audio(
    model_name: str,
    aiohttp_session: aiohttp.ClientSession,
    send_url_only: bool = False,
    **additional_client_args
) -> Union[list, str]:
        # Check if we have aiohttp session supplied or use the default one
        if aiohttp_session:
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
        _audios_in_bytes = []


        if send_url_only:
            return _result["audio"]["url"]
        else:
            # Download audios
            async with _aiohttp_session.get(_result["audio"]["url"]) as response:
                if response.status == 200:
                    _audio_data = await response.read()
                    
                    # Send the audio
                    _audios_in_bytes.append(_audio_data)
                else:
                    raise ValueError(f"Failed to download audio from {_result['audio']['url']}, status code: {response.status}")

            # Cleanup
            return _audios_in_bytes
        