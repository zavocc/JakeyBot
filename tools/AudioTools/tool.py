from .manifest import ToolManifest
from os import environ
import aiofiles.os
import aiohttp
import asyncio
import discord
import importlib
import io

# Function implementations
class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()

        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def _tool_function_audio_editor(self, discord_attachment_url: str, prompt: str, edit_start_in_seconds: int = 3, edit_length_in_seconds: int = 5):
        # Validate parameters
        if edit_length_in_seconds > 10 or edit_length_in_seconds < 0.5:
            edit_length_in_seconds = 5

        # Import
        _gradio_client = importlib.import_module("gradio_client")
        
        _message_curent = await self.method_send("🎤✨ Adding some magic to the audio...")
        _result = await asyncio.to_thread(
            _gradio_client.Client("OpenSound/EzAudio").predict,
            text=prompt,
            boundary=2,
            gt_file=_gradio_client.handle_file(discord_attachment_url),
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
        await _message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=_result))

        # Cleanup
        await aiofiles.os.remove(_result)
        return "Audio editing success"
    
    # Audio generator using PlayHT Groq Voices
    async def _tool_function_audio_generator(self, text: str, voice: str = "Atlas"):
        # Check if GROQ_API_KEY is set
        if not environ.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is not set, please set it in the environment variables")

        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {environ.get('GROQ_API_KEY')}"
        }
        _payload = {
            "model": "playai-tts",
            "voice": f"{voice}-PlayAI",
            "input": text,
            "response_format": "wav"
        }
        # Endpoint
        _endpoint = "https://api.groq.com/openai/v1/audio/speech"

        # Send the request to Groq
        async with _client_session.post(_endpoint, headers=_headers, json=_payload) as response:
            if response.status != 200:
                raise Exception(f"Error: {response.status} - {await response.text()}")

            # Check if mime type is audio/wav
            if "audio/wav" not in response.headers["Content-Type"]:
                raise Exception("The response from Groq is not in audio/wav format")

            # Read the audio data
            _audio = await response.read()

        # Send the audio
        await self.method_send(file=discord.File(fp=io.BytesIO(_audio), filename="voice.wav"))

        # Cleanup
        return "Audio success and the file should be sent automatically"
    
    async def _tool_function_voice_cloner(self, discord_attachment_url: str, text: str):
        # Import
        _gradio_client = importlib.import_module("gradio_client")
        
        message_curent = await self.method_send("🗣️ Ok... please wait while I'm cloning the voice")
        result = await asyncio.to_thread(
            _gradio_client.Client("tonyassi/voice-clone").predict,
            text=text,
            audio=_gradio_client.file(discord_attachment_url),
            api_name="/predict"
        )
        
        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Audio editing success"

