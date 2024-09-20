# Huggingface spaces endpoints 
import google.generativeai as genai
import asyncio
import discord
import gradio_client
import os

# Function implementations
class Tool:
    tool_human_name = "Background Remover"
    tool_name = "background_remover"
    attachments_required = True
    tool_config = {'function_calling_config':'ANY'}
    file_url = None
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        # Image generator
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Remove background from an image",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'prompt':genai.protos.Schema(type=genai.protos.Type.STRING),
                        },
                        required=['prompt']
                    )
                )
            ]
        )

    # Image generator
    async def _tool_function(self, *args, **kwargs):
        print(self.file_url)
        if self.file_url is None:
            return "Please add images to your prompt"

        # Create image
        try:
            result = await asyncio.to_thread(
                gradio_client.Client("not-lain/background-removal").predict,
                image=gradio_client.handle_file(self.file_url),
                api_name="/image"
            )
        except Exception as e:
            return f"Background removal fail and the image isn't sent, reason {e}"

        # Send the image
        await self.ctx.send(file=discord.File(fp=result[0]))

        # Cleanup
        os.remove(result[0])
        return "Background removal successful and the file should be sent automatically"
