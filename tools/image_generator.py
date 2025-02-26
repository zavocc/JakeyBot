from os import environ
import aiohttp
import asyncio
import discord
import io

# Function implementations
class Tool:
    tool_human_name = "Image Generator with Stable Diffusion 3.5"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "image_generator_sd",
                "description": "Generate or restyle images using natural language or from description using Stable Diffusion 3.5",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_description": {
                            "type": "STRING",
                            "description": "The prompt of the image to generate"
                        }
                    },
                    "required": ["image_description"]
                }
            },
            {
                "name": "image_generator_imagen",
                "description": "Create high quality images using Google's latest state-of-the-art Imagen 3 model",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_description": {
                            "type": "STRING",
                            "description": "The prompt of the image to generate. It's recommended to enhance the prompt as the model is prompt-sensitive."
                        },
                        "aspect_ratio": {
                            "type": "STRING",
                            "description": "The aspect ratio of the image to generate",
                            "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"]
                        },
                        "negative_prompt": {
                            "type": "STRING",
                            "description": "Which elements shall not include, when the user asks not to add something, specify the prompts here. It's recommended to separate each elements as comma-separated values, it's also recommended to add common bad attributes of the image here."
                        }
                    },
                    "required": ["image_description"]
                }
            }
        ]

    # Image generator
    async def _tool_function_image_generator_sd(self, image_description: str):
        # Check if HF_TOKEN is set
        if not environ.get("HF_TOKEN"):
            raise ValueError("HuggingFace API token is not set, please set it in the environment variables")

        # Create image
        message_curent = await self.method_send(f"⌛ Generating **{image_description}**... this may take few minutes")
        
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Payload
        _payload = {
            "inputs": image_description,
        }

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {environ.get('HF_TOKEN')}"
        }

        # Make a request
        async with _client_session.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo", json=_payload, headers=_headers) as _response:
            # Check if the response is not 200 which may print JSON
            # Response 200 would return the binary image
            if _response.status != 200:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Send the image
            _imagedata = await _response.content.read()

        # Delete status
        await message_curent.delete()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_imagedata), filename="generated_image.png"))

        # Cleanup
        return "Image generation success and the file should be sent automatically"
    
    async def _tool_function_image_generator_imagen(self, image_description: str, aspect_ratio: str = "1:1", negative_prompt: str = None):
        # Check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("FAL.AI API token is not set, please set it in the environment variables")

        # Create image
        _embed = discord.Embed(
            description="**Please wait while creating an image**\nTip: create an image of a Ben 10 alien that resembles a fox but has a flames on his back with omnitrix symbol in his chest",
        )
        _embed.set_footer(text=image_description)
        _embed.set_image(url="https://cdn.discordapp.com/attachments/1264228477272457327/1343477258492448830/generated_image.png")

        _message_curent = await self.method_send(embed=_embed)
        
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Payload
        _payload = {
            "prompt": image_description,
            "aspect_ratio": aspect_ratio,
            "num_images": 1,
        }

        if negative_prompt:
            _payload["negative_prompt"] = negative_prompt

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Key {environ.get('FAL_KEY')}"
        }

        # Make a request
        async with _client_session.post("https://queue.fal.run/fal-ai/imagen3", json=_payload, headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Get the request ID
            _status = await _response.json()

        # We need to loop through the status endpoint until it is completed
        while True:
            async with _client_session.get(f"https://queue.fal.run/fal-ai/imagen3/requests/{_status['request_id']}/status", headers=_headers) as _response:
                # Error code beyond 202 is not successful
                if _response.status > 202:
                    raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
                
                # Send the image
                _status = await _response.json()

                # Check if we can deserialize it
                if _status["status"] == "COMPLETED":
                    break

                # Wait for 2.5 seconds
                await asyncio.sleep(2.5)

        # Get the image
        async with _client_session.get(f"https://queue.fal.run/fal-ai/imagen3/requests/{_status["request_id"]}", headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Send the image
            _status = await _response.json()

            # Check if we can deserialize it
            if len(_status["images"]) == 0:
                raise Exception("Failed to generate image, no images had been generated")
        
        # Set thumbnail again
        _embed.set_image(url=_status["images"][0]["url"])
        _embed.description = None
        await _message_curent.edit("Your image is ready", embed=_embed)

        # Cleanup
        return "Image generation success and the file should be sent automatically"