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
    async def tool_imagen_image_gen(self, prompt: str, aspect_ratio: str = "1:1", resolution: str = "1K", negative_prompt: str = None):
        # Create image
        _message_curent = await self.discord_message.channel.send(f"⌛ Generating image using Imagen 4 with prompt **{prompt}**")
        
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

        logging.info("Using Imagen 4 model for generation")
        _params.update({
            "aspect_ratio": aspect_ratio,
            "resolution": resolution
        })

        if negative_prompt:
            _params["negative_prompt"] = negative_prompt

        # Generate image
        _discordImageURLs = []
        _imagesInBytes = await run_image(
            model_name="imagen4/preview/ultra",
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

            _sentImg = await self.discord_message.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
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

    async def tool_gpt_image_gen(self, prompt: str, image_url: list = None, image_size: str = "auto", quality: str = "auto", background: str = "auto", input_fidelity: str = "high"):
        # Create image
        _message_curent = await self.discord_message.channel.send(f"⌛ Generating image using GPT-4o with prompt **{prompt}**")

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

        logging.info("Using GPT-4o model for generation")
        _params.update({
            "image_size": image_size,
            "quality": quality,
            "background": background
        })

        # Check if image_url is provided
        if image_url:
            _model_endpoint = "gpt-image-1/edit-image"
            _params["image_urls"] = image_url
            _params["input_fidelity"] = input_fidelity
        else:
            _model_endpoint = "gpt-image-1/text-to-image"

        # Generate image
        _discordImageURLs = []
        _imagesInBytes = await run_image(
            model_name=_model_endpoint,
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

            _sentImg = await self.discord_message.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
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
    
    async def tool_nb_pro_image_gen(self, prompt: str, image_url: list = None, aspect_ratio: str = "16:9", resolution: str = "2K", enable_web_search: bool = False):
        # Create image
        if enable_web_search:
            _message_curent = await self.discord_ctx.channel.send(f"🔍 Searching the web for information and generating an image using Nano Banana Pro with prompt **{prompt}**")
        else:
            _message_curent = await self.discord_ctx.channel.send(f"🍌 Generating image using Nano Banana Pro with prompt **{prompt}**")

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

        logging.info("Using Nano Banana Pro model for generation")
        _params.update({
            "aspect_ratio": aspect_ratio,
            "num_images": 1,
            "output_format": "png",
            "resolution": resolution,
            "enable_web_search": enable_web_search
        })

        # Check if image_url is provided
        if image_url:
            _model_endpoint = "nano-banana-pro/edit"
            _params["image_urls"] = image_url
        else:
            _model_endpoint = "nano-banana-pro"

        # Generate image
        _discordImageURLs = []

        # If 4k was set, we use embeds
        if resolution == "4K":
            _useEmbeds = True
        else:
            _useEmbeds = False
        _imagesInBytes = await run_image(
            model_name=_model_endpoint,
            aiohttp_session=_aiohttp_client_session,
            send_url_only=_useEmbeds,
            **_params
        )

        # Send the image and add each of the discord message to the list so we can add it as context later
        for _images in _imagesInBytes:
            # Filename
            _fileName = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_nbpro.png"

            if _useEmbeds:
                # Upload to discord as embed
                _embed = discord.Embed(title="🍌 Generated Nano Banana Pro Image.", color=discord.Colour.yellow())
                _embed.set_footer(text="Powered by Nano Banana Pro (also known as Gemini 3 Pro Image)")
                _embed.set_image(url=_images)
                await self.discord_ctx.channel.send(embed=_embed)
                _discordImageURLs.append(_images)

            else:
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
    async def tool_nb_sd_image_editor(self, prompt: str, image_url: list[str], enable_safety_checker: bool = True, model: str = "gemini-25-flash-image"):
        # Create image
        _message_curent = await self.discord_message.channel.send(f"⌛ I will now edit the images with prompt **{prompt}**... this may take few minutes")
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Image Editing tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        # Construct params
        _additional_params = {"prompt": prompt, "image_urls": image_url}

        # Output in 4k for seedream 
        if model == "bytedance/seedream/v4/edit":
            logging.info("Using Seedream 4 model for editing, setting width and height to 4K")
            _additional_params.update({
                "enable_safety_checker": enable_safety_checker,
                "image_size": {
                    "width": 3840,
                    "height": 2160
                }
            })
        else:
            logging.info("Using Gemini 2.5 Flash model for editing")

        # Generate image
        _discordImageURLs = []
        _imagesInBytes = await run_image(
            model_name=model,
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

            _sentImg = await self.discord_message.channel.send(file=discord.File(io.BytesIO(_images), filename=_fileName))
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