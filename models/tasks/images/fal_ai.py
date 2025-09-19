from os import environ
import aiohttp
import fal_client

# This method outputs bytes
async def run(
    prompt: str,
    model_name: str,
    image_urls: list = None,
    negative_prompt: str = None,
    aiohttp_session: aiohttp.ClientSession = None,
    **additional_client_args
) -> list :
        # Check if we have aiohttp session supplied or use the default one
        if aiohttp_session:
            _aiohttp_session = aiohttp_session
        else:
            _aiohttp_session = aiohttp.ClientSession()
    
        # check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("FAL_KEY is not set! Cannot proceed generating images")
        
        # Construct params
        _params = {
            "prompt": prompt
        }
        _endpoint = f"fal-ai/{model_name}"

        # Check if we have reference images
        if image_urls:
            _params["image_urls"] = image_urls
            _endpoint = f"fal-ai/{model_name}/edit"

        if negative_prompt:
             _params["negative_prompt"] = negative_prompt


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
    