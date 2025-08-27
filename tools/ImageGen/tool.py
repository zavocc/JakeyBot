from .manifest import ToolManifest
from os import environ
import datetime
import discord
import fal_client
import io

class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Image generator
    async def _tool_function(self, prompt: str, url_context: list[str] = None):
        # Create image
        _message_curent = await self.method_send(f"⌛ Generating with prompt **{prompt}**... this may take few minutes")
        
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")

        # check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("❌ FAL_KEY is not set! Cannot proceed generating images")
        
        # Construct params
        _params = {
            "prompt": prompt
        }
        _endpoint = "fal-ai/gemini-25-flash-image"

        if url_context:
            _params["image_urls"] = url_context
            _endpoint = "fal-ai/gemini-25-flash-image/edit"

        # Generate an image
        _status = await fal_client.submit_async(
            _endpoint,
            arguments = _params
        )

        # Wait for the result
        _result = await _status.get()

        # URLs of images
        _url_aware = []

        # Download images
        for _images in _result["images"]:
            async with self.discord_bot._aiohttp_main_client_session.get(_images["url"]) as response:
                if response.status == 200:
                    _image_data = await response.read()
                   
                    # Send the image
                    _msgID = await self.method_send(file=discord.File(fp=io.BytesIO(_image_data), filename=f"generated_image_{datetime.datetime.now().strftime('%H_%M_%S_%m%d%Y_%s')}.png"))
                    _url_aware.append(_msgID.attachments[0].url)
                else:
                    raise ValueError(f"❌ Failed to download image from {_images}, status code: {response.status}")
        

        # Delete status
        await _message_curent.delete()

        # Cleanup
        return {
            "guidelines": "The image is already sent to the UI, no need to print the URLs as it will just cause previews to display images twice.",
            "context_results": _url_aware,
            "status": "Image generated successfully"
        }