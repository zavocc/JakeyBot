from .manifest import ToolManifest
from os import environ
import aiohttp
import base64
import datetime
import discord
import io

class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Image generator
    async def _tool_function(self, prompt: str, discord_attachment_url: str = None, size: str = "1024x1024"):
        # Create image
        _message_curent = await self.method_send(f"⌛ Generating with prompt **{prompt}**... this may take few minutes")

        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if AZURE_AI_FLUX_ENDPOINT and AZURE_AI_FLUX_KEY are set
        if not environ.get("AZURE_AI_FLUX_ENDPOINT") or not environ.get("AZURE_AI_FLUX_KEY"):
            raise ValueError("Environment variables AZURE_AI_FLUX_ENDPOINT and AZURE_AI_FLUX_KEY must be set for image generation")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Use appropriate endpoints - Fixed URL construction
        if discord_attachment_url:
            _endpoint_url = environ.get("AZURE_AI_FLUX_ENDPOINT") + "/images/edits"
        else:
            _endpoint_url = environ.get("AZURE_AI_FLUX_ENDPOINT") + "/images/generations"

        # Headers - Fixed header name to match control code
        _headers = {
            "Api-Key": environ.get("AZURE_AI_FLUX_KEY"),
            "x-ms-model-mesh-model-name": "FLUX.1-Kontext-pro", 
        }

        # Parameters - Fixed to use query parameters
        _params = {
            "api-version": "2025-04-01-preview"
        }

        # Download the image if needed        
        if discord_attachment_url:
            async with _client_session.head(url=discord_attachment_url) as _response:
                _content_length = int(_response.headers.get("Content-Length", 0))

                if _content_length == 0:
                    raise ValueError("The image size is zero or invalid, please provide a valid image")
                
                # Check if the mime type is image
                _mime_type = _response.headers.get("Content-Type", None)
                if not _mime_type or not _mime_type.startswith("image"):
                    raise ValueError("The file is not an image, please provide an image file")

                if _content_length > 10 * 1024 * 1024:
                    raise ValueError("The image size is too large, please provide an image that is less than 10MB")
                
            # Download the image
            async with _client_session.get(discord_attachment_url) as _response:
                _imagedata = await _response.read()

        # Prepare request data based on endpoint type
        if discord_attachment_url:
            # For edit endpoint: use form data with file upload
            _form = aiohttp.FormData()
            _form.add_field(
                name="image",
                value=io.BytesIO(_imagedata),
                filename="image.png",
                content_type="image/png"
            )
            _form.add_field("prompt", prompt)
            _form.add_field("n", "1")
            _form.add_field("size", size)
            
            _data = _form
            _json = None
        else:
            # For generation endpoint: use JSON
            _data = None
            _json = {
                "prompt": prompt,
                "n": 1,
                "size": size,
                "output_format": "png"
            }
            _headers["Content-Type"] = "application/json"

        # Make the request
        async with _client_session.post(
            url=_endpoint_url,
            data=_data,
            json=_json,
            headers=_headers,
            params=_params
        ) as _response:
            if _response.status != 200:
                raise ValueError(f"Failed to generate image, status code: {_response.status}, response: {(await _response.text())}")

            _iresponses = await _response.json()

        # Send and decode
        _file_format = datetime.datetime.now().strftime("%H_%M_%S_%m%d%Y_%s")

        _imgdata = _iresponses["data"][0]["b64_json"]
        _discord_img_sent = await self.method_send(
            file=discord.File(io.BytesIO(base64.b64decode(_imgdata)), 
                            filename=f"generated_image{_file_format}_image_part.png")
        )
        
        # Response
        _responses = {
            "NOTICE": "Do not send the link to the end user, as the image is already sent from the backend, sending it would cause the image to display again",
            "generatedImageDiscordURL": _discord_img_sent.attachments[0].url,
            "fileName": _discord_img_sent.attachments[0].filename,
            "createdTime": _file_format,
        }

        # Delete status
        await _message_curent.delete()

        # Cleanup
        return _responses