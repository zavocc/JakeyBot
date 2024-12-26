from os import environ
import aiohttp
import discord
import io

# Function implementations
class Tool:
    tool_human_name = "Image Generator with Stable Diffusion 3.5"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "name": "image_generator",
            "description": "Generate or restyle images using natural language or from description",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "image_description": {
                        "type": "STRING"
                    }
                },
                "required": ["image_description"]
            }
        }

    # Image generator
    async def _tool_function(self, image_description: str):
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
