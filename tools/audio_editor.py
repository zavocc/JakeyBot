# Huggingface spaces endpoints 
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "EzAudio"

    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "audio_editor",
                "description": "Edit audio, simply provide the description for editing, and EzAudio will do the rest",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The discord attachment URL of the audio file"
                        },
                        "prompt": {
                            "type": "STRING",
                            "description": "The prompt for the model to add elements to the audio"
                        },
                        "edit_start_in_seconds": {
                            "type": "NUMBER",
                            "description": "The start time in seconds to edit the audio"
                        },
                        "edit_length_in_seconds": {
                            "type": "NUMBER",
                            "description": "The length in seconds to edit the audio"
                        }
                    },
                    "required": ["discord_attachment_url", "prompt"]
                }
            }
        ]

    async def _tool_function(self, discord_attachment_url: str, prompt: str, edit_start_in_seconds: int = 3, edit_length_in_seconds: int = 5):
        # Validate parameters
        if edit_length_in_seconds > 10 or edit_length_in_seconds < 0.5:
            edit_length_in_seconds = 5

        # Import
        gradio_client = importlib.import_module("gradio_client")
        
        message_curent = await self.method_send("🎤✨ Adding some magic to the audio...")
        result = await asyncio.to_thread(
            gradio_client.Client("OpenSound/EzAudio").predict,
            text=prompt,
            boundary=2,
            gt_file=gradio_client.handle_file(discord_attachment_url),
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
        
        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Audio editing success"
