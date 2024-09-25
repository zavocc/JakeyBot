# Huggingface spaces endpoints 
import google.generativeai as genai
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "Image Generator with Stable Diffusion 3"
    tool_name = "image_generator"
    tool_config = "AUTO"
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        # Image generator
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Generate or restyle images using natural language or from description",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'image_description':genai.protos.Schema(type=genai.protos.Type.STRING),
                            'width':genai.protos.Schema(type=genai.protos.Type.NUMBER),
                            'height':genai.protos.Schema(type=genai.protos.Type.NUMBER)
                        },
                        required=['image_description', 'width', 'height']
                    )
                )
            ]
        )

    # Image generator
    async def _tool_function(self, image_description: str, width: int, height: int):
        # Validate parameters, width and height should not exceed 1344 and should not be set to 0
        if width > 1344 or width == 0 or height > 1344 or height == 0:
            height, width = 1024, 1024

        # Import
        try:
            gradio_client = importlib.import_module("gradio_client")
            os = importlib.import_module("os")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        # Create image
        try:
            message_curent = await self.ctx.send("⌛ Generating an image... this may take few minutes")
            result = await asyncio.to_thread(
                gradio_client.Client("stabilityai/stable-diffusion-3-medium").predict,
                prompt=image_description,
                negative_prompt=f"low quality, distorted, bad art, strong violence, sexually explicit, disturbing",
                width=width,
                height=height,
                guidance_scale=7,
                seed=0,
                randomize_seed=True,
                num_inference_steps=30,
                api_name="/infer"
            )
        except Exception as e:
            return f"Image generation fail and the image isn't sent, reason {e}"
        
        # Delete status
        await message_curent.delete()

        # Send the image
        await self.ctx.send(file=discord.File(fp=result[0]))

        # Cleanup
        await aiofiles.os.remove(result[0])
        return "Image generation success and the file should be sent automatically"
