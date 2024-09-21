# Huggingface spaces endpoints 
import google.generativeai as genai
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "EzAudio"
    tool_name = "audio_editor"
    tool_config = "AUTO"

    # File path attribute
    file_uri = ""

    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        # Image generator
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Edit audio, simply provide the description for editing, and EzAudio will do the rest",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'prompt':genai.protos.Schema(type=genai.protos.Type.STRING),
                            'edit_start_in_seconds':genai.protos.Schema(type=genai.protos.Type.NUMBER),
                            'edit_length_in_seconds':genai.protos.Schema(type=genai.protos.Type.NUMBER)
                        },
                        required=['prompt']
                    )
                )
            ]
        )

    async def _tool_function(self, prompt: str, edit_start_in_seconds: int = 3, edit_length_in_seconds: int = 5):
        # Validate parameters
        if edit_length_in_seconds > 10 or edit_length_in_seconds < 0.5:
            edit_length_in_seconds = 5

        # Import
        try:
            gradio_client = importlib.import_module("gradio_client")
            os = importlib.import_module("os")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        # Create image
        try:
            message_curent = await self.ctx.send("🎤✨ Adding some magic to the audio...")
            result = await asyncio.to_thread(
                gradio_client.Client("OpenSound/EzAudio").predict,
                text=prompt,
                boundary=2,
                gt_file=gradio_client.handle_file(self.file_uri),
                mask_start=edit_start_in_seconds,
                mask_length=edit_length_in_seconds,
                guidance_scale=5,
                guidance_rescale=0,
                ddim_steps=50,
                eta=1,
                random_seed=0,
                randomize_seed=True,
                api_name="/editing_audio_1"
            )
        except Exception as e:
            return f"I can't edit the audio, reason {e}"
        
        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.ctx.send(file=discord.File(fp=result))

        # Cleanup
        os.remove(result)
        return "Audio editing success"
