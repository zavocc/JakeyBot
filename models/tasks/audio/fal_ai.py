from os import environ
import aiohttp
import fal_client

# This method outputs bytes
async def run(
    prompt: str,
    model_name: str,
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
            raise ValueError("FAL_KEY is not set! Cannot proceed generating audios")
        
        # Construct params
        _params = {
            "prompt": prompt
        }
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

        # Download audios
        for _audios in _result["audio"]:
            async with _aiohttp_session.get(_audios["url"]) as response:
                if response.status == 200:
                    _audio_data = await response.read()
                   
                    # Send the audio
                    _audios_in_bytes.append(_audio_data)
                else:
                    raise ValueError(f"Failed to download audio from {_audios}, status code: {response.status}")

        # Cleanup
        return _audios_in_bytes
    