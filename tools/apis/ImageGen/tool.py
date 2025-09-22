from models.tasks.media.fal_ai import run_image
import aiohttp
import datetime
import discord
import filetype
import io
import logging

class Tools:
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Image generator
    async def tool_image_generator(self, prompt: str, aspect_ratio: str = "1:1", resolution: str = "1K", negative_prompt: str = None, enable_safety_checker: bool = True, model: str = "imagen4/preview/ultra"):
        # Create image
        _message_curent = await self.method_send(f"⌛ Generating with prompt **{prompt}**... this may take few minutes")
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Image Generation tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.info("No aiohttp instance found in discord bot subclass, creating a new one for Image Generation tool")
            _aiohttp_client_session = aiohttp.ClientSession()

        # Initialize _params with default empty dict
        _params = {}

        # Update parameters for SeeDream 4
        if model == "imagen4/preview/ultra":
            logging.info("Using Imagen 4 model for generation and passing negative prompt")
            negative_prompt = negative_prompt
            _params = {
                "aspect_ratio": aspect_ratio,
                "resolution": resolution
            }
        elif model == "bytedance/seedream/v4/text-to-image":
            logging.info("Using Seedream 4 model for generation, setting width and height to 4096 and disabling negative prompt")
            negative_prompt = None
            _params = {
                "enable_safety_checker": enable_safety_checker,
                "image_size": {
                    "width": 3840,
                    "height": 2160
                }
            }

        # Generate image
        _discordImageURLs = []
        _imagesInBytes = await run_image(
            prompt=prompt,
            model_name=model,
            negative_prompt=negative_prompt,
            aiohttp_session=_aiohttp_client_session,
            **_params
        )

        # Send the image and add each of the discord message to the list so we can add it as context later
        for _index, _images in enumerate(_imagesInBytes):
            # Check the image type
            _magicType = filetype.guess(_images)
            if _magicType.mime == "image/jpeg":
                _formatExtension = "jpg"
            elif _magicType.mime == "image/png":
                _formatExtension = "png"
            elif _magicType.mime == "image/webp":
                _formatExtension = "webp"
            else:
                _formatExtension = "bin"

            # Filename
            _fileName = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_index_{_index}.{_formatExtension}"

            _sentImg = await self.discord_ctx.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
            _discordImageURLs.append(_sentImg.attachments[0].url)
            

        # Delete the _imagesInBytes to save memory
        del _imagesInBytes

        # Delete status
        await _message_curent.delete()

         # Cleanup
        return {
            "guidelines": "The image is already sent to the UI, no need to print the URLs as it will just cause previews to display images twice.",
            "context_results": _discordImageURLs,
            "status": "Image generated successfully"
        }
    
    # Image editor
    async def tool_image_editor(self, prompt: str, image_url: list[str], enable_safety_checker: bool = True, model: str = "gemini-25-flash-image"):
        # Create image
        _message_curent = await self.method_send(f"⌛ I will now edit the images with prompt **{prompt}**... this may take few minutes")
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Image Editing tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.info("No aiohttp instance found in discord bot subclass, creating a new one for Image Editing tool")
            _aiohttp_client_session = aiohttp.ClientSession()
        
        # Output in 4k for seedream 
        if model == "bytedance/seedream/v4":
            logging.info("Using Seedream 4 model for editing, setting width and height to 4096")
            _additional_params = {
                "enable_safety_checker": enable_safety_checker,
                "image_size": {
                    "width": 3840,
                    "height": 2160
                }
            }
        else:
            logging.info("Using Gemini 2.5 Flash model for editing")
            _additional_params = {}

        # Generate image
        _discordImageURLs = []
        _imagesInBytes = await run_image(
            prompt=prompt,
            model_name=model,
            image_urls=image_url,
            aiohttp_session=_aiohttp_client_session,
            **_additional_params
        )

        # Send the image and add each of the discord message to the list so we can add it as context later
        for _index, _images in enumerate(_imagesInBytes):
            # Check the image type
            _magicType = filetype.guess(_images)
            if _magicType.mime == "image/jpeg":
                _formatExtension = "jpg"
            elif _magicType.mime == "image/png":
                _formatExtension = "png"
            elif _magicType.mime == "image/webp":
                _formatExtension = "webp"
            else:
                _formatExtension = "bin"

            # Filename
            _fileName = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_index_{_index}.{_formatExtension}"

            _sentImg = await self.discord_ctx.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
            _discordImageURLs.append(_sentImg.attachments[0].url)
            

        # Delete the _imagesInBytes to save memory
        del _imagesInBytes

        # Delete status
        await _message_curent.delete()

         # Cleanup
        return {
            "guidelines": "The image is already sent to the UI, no need to print the URLs as it will just cause previews to display images twice.",
            "context_results": _discordImageURLs,
            "status": "Image generated successfully"
        }