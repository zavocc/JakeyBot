# Huggingface spaces endpoints 
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "Image to Line drawing"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "image_to_linedrawing",
                "description": "Restyle images to line drawings based from the given image",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The discord attachment URL of the image file"
                        },
                        "mode": {
                            "type": "STRING",
                            "enum": ["Simple Lines", "Complex Lines"],
                            "description": "The style of the line drawing, use your image analysis capabilities to see which suites best for conversion. Use simple lines for images that look simple and animated, complex for detailed images"
                        }
                    },
                    "required": ["discord_attachment_url", "mode"]
                }
            }
        ]


    async def _tool_function(self, discord_attachment_url: str, mode: str):
        # Import
        gradio_client = importlib.import_module("gradio_client")

        result = await asyncio.to_thread(
            gradio_client.Client("awacke1/Image-to-Line-Drawings").predict,
            input_img=gradio_client.handle_file(discord_attachment_url),
            ver=mode,
            api_name="/predict"
        )
    
        # Send the image
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Image restyling success and the file should be sent automatically"
