# Huggingface spaces endpoints 
import google.generativeai as genai
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "Image to Line drawing"
    tool_name = "image_to_linedrawing"
    def __init__(self, method_send):
        self.method_send = method_send

        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Restyle images to line drawings based from the given image",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'discord_attachment_url':genai.protos.Schema(type=genai.protos.Type.STRING),
                            'mode':genai.protos.Schema(type=genai.protos.Type.STRING, enum=["Simple Lines", "Complex Lines"]),
                        },
                        required=['discord_attachment_url', 'mode']
                    )
                )
            ]
        )

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
