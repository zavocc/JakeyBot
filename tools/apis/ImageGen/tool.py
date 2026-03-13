from models.tasks.media.fal_ai import run_image
import aiohttp
import datetime
import discord
import filetype
import io
import logging

class Tools:
    def __init__(self, discord_message, discord_bot):
        self.discord_message = discord_message
        self.discord_bot = discord_bot

    # Image generator
    async def tool_gpt_image_gen(self, prompt: str, image_url: list = None, image_size: str = "auto", quality: str = "auto", background: str = "auto", input_fidelity: str = "high"):
        # Create image
        _message_curent = await self.discord_message.channel.send(f"⌛ Generating image using GPT Images 1.5 with prompt **{prompt}**")

        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Image Generation tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        # Initialize _params with default empty dict
        _params = {
            "prompt": prompt
        }

        logging.info("Using GPT Images 1.5 model for generation")
        _params.update({
            "image_size": image_size,
            "quality": quality,
            "background": background
        })

        # Check if image_url is provided
        if image_url:
            _model_endpoint = "gpt-image-1.5/edit-image"
            _params["image_urls"] = image_url
            _params["input_fidelity"] = input_fidelity
        else:
            _model_endpoint = "gpt-image-1.5/text-to-image"

        # Generate image
        _imagesInBytesPayload = await run_image(
            model_name=_model_endpoint,
            aiohttp_session=_aiohttp_client_session,
            **_params
        )
        _imagesInBytes = _imagesInBytesPayload["images_in_bytes"]

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

            await self.discord_message.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
            

        # Delete the _imagesInBytes to save memory
        del _imagesInBytes

        # Delete status
        await _message_curent.delete()

         # Cleanup
        return {
            "guidelines": "The image is already sent to the UI, no need to print the URLs as it will just cause previews to display images twice.",
            "context_results": _imagesInBytesPayload["images_urls"],
            "status": "Image generated successfully"
        }

    async def tool_nano_banana_ii_gen(self, prompt: str, image_url: list = None, aspect_ratio: str = "16:9", resolution: str = "2K", enable_web_search: bool = False):
        # Create image
        if enable_web_search:
            _message_curent = await self.discord_message.channel.send(f"🔍 Searching the web for information and generating an image using Nano Banana 2 with prompt **{prompt}**")
        else:
            _message_curent = await self.discord_message.channel.send(f"🍌 Generating image using Nano Banana 2 with prompt **{prompt}**")

        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Image Generation tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        # Initialize _params with default empty dict
        _params = {
            "prompt": prompt
        }

        logging.info("Using Nano Banana 2 model for generation")
        _params.update({
            "aspect_ratio": aspect_ratio,
            "num_images": 1,
            "output_format": "png",
            "resolution": resolution,
            "enable_web_search": enable_web_search
        })

        # Check if image_url is provided
        if image_url:
            _model_endpoint = "nano-banana-2/edit"
            _params["image_urls"] = image_url
        else:
            _model_endpoint = "nano-banana-2"

        # If 4k was set, we use embeds
        _useEmbeds = resolution == "4K"
        _imagesInBytesPayload = await run_image(
            model_name=_model_endpoint,
            aiohttp_session=_aiohttp_client_session,
            send_bytes=not _useEmbeds,
            **_params
        )
        _falImageURLs = _imagesInBytesPayload["images_urls"]

        # Send the image. For 4K, send embed URL directly from FAL.
        if _useEmbeds:
            for _image_url in _falImageURLs:
                _embed = discord.Embed(title="🍌 Generated Nano Banana 2 Image.", color=discord.Colour.yellow())
                _embed.set_footer(text="Powered by Nano Banana 2 (also known as Gemini 3.1 Flash Image)")
                _embed.set_image(url=_image_url)
                await self.discord_message.channel.send(embed=_embed)
        else:
            _imagesInBytes = _imagesInBytesPayload["images_in_bytes"]
            for _images in _imagesInBytes:
                # Filename
                _fileName = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_nb2.png"
                await self.discord_message.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))

            # Delete the _imagesInBytes to save memory
            del _imagesInBytes

        # Delete status
        await _message_curent.delete()

         # Cleanup
        return {
            "guidelines": "The image is already sent to the UI, no need to print the URLs as it will just cause previews to display images twice.",
            "context_results": _imagesInBytesPayload["images_urls"],
            "status": "Image generated successfully"
        }