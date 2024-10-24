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
    tool_config = "AUTO"
    file_uri = ""
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Restyle images to line drawings based from the given image",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'mode':genai.protos.Schema(type=genai.protos.Type.STRING, enum=["Simple Lines", "Complex Lines"]),
                        },
                        required=['mode']
                    )
                )
            ]
        )

    async def _tool_function(self, mode: str):
        # Import
        try:
            gradio_client = importlib.import_module("gradio_client")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        try:
            result = await asyncio.to_thread(
                gradio_client.Client("awacke1/Image-to-Line-Drawings").predict,
                input_img=gradio_client.handle_file(self.file_uri),
                ver=mode,
                api_name="/predict"
            )
        except Exception as e:
            return f"Image restyling failed and the image isn't sent, reason {e}"
    

        # Send the image
        if isinstance(self.ctx, discord.Message):
            await self.ctx.channel.send_message(file=discord.File(fp=result))
        else:
            await self.ctx.send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Image restyling success and the file should be sent automatically"
