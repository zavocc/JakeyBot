# Huggingface spaces endpoints 
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool:
    tool_human_name = "Voice Cloner"
    tool_name = "voice_cloner"

    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "name": self.tool_name,
            "description": "Clone voices and perform TTS tasks from the given audio files",
            "parameters": {
                "type": "object",
                "properties": {
                    "discord_attachment_url": {
                        "type": "string"
                    },
                    "text": {
                        "type": "string"
                    }
                },
                "required": ["discord_attachment_url", "text"]
            }
        }

    async def _tool_function(self, discord_attachment_url: str, text: str):
        # Import
        gradio_client = importlib.import_module("gradio_client")
        
        message_curent = await self.method_send("🗣️ Ok... please wait while I'm cloning the voice")
        result = await asyncio.to_thread(
            gradio_client.Client("tonyassi/voice-clone").predict,
            text=text,
            audio=gradio_client.file(discord_attachment_url),
            api_name="/predict"
        )
        
        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Audio editing success"
