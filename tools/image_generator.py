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
                "description": "Generate or restyle images using natural language or from description using Google's Imagen 3 model",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_description": {
                            "type": "STRING",
                            "description": "The prompt of the image to generate"
                        },
                        "aspect_ratio": {
                            "type": "STRING",
                            "description": "The aspect ratio of the image to generate",
                            "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"]
                        },
                        "negative_prompt": {
                            "type": "STRING",
                            "description": "Which elements shall not include, when the user asks not to add something, specify the prompts here. It's recommended to separate each elements as comma-separated values"
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
        message_curent = await self.method_send(f"⌛ Generating **{image_description}**... this may take few minutes")
        
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

        # TODO: Get the result and loop through status endpoint
        #curl --request GET \
        #--url https://queue.fal.run/fal-ai/imagen3/requests/$REQUEST_ID/status \
        #--header "Authorization: Key $FAL_KEY"
        #{"status": "COMPLETED", "request_id": "2f18c428-88c7-4ad4-99b8-77483651dff6", "response_url": "https://queue.fal.run/fal-ai/imagen3/requests/2f18c428-88c7-4ad4-99b8-77483651dff6", "status_url": "https://queue.fal.run/fal-ai/imagen3/requests/2f18c428-88c7-4ad4-99b8-77483651dff6/status", "cancel_url": "https://queue.fal.run/fal-ai/imagen3/requests/2f18c428-88c7-4ad4-99b8-77483651dff6/cancel", "logs": null, "metrics": {"inference_time": 9.276242017745972}

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

        # Ensure it is sent as image
        _headers.pop("Content-Type")

        # Download the image
        async with _client_session.get(_status["images"][0]["url"], headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Send the image
            _imagedata = await _response.content.read()
        
        # Delete status
        await message_curent.delete()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_imagedata), filename="generated_image.png"))

        # Cleanup
        return "Image generation success and the file should be sent automatically"