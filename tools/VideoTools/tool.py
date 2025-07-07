from .manifest import ToolManifest
import aiofiles.os
import asyncio
import discord
import importlib

# Function implementations
class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()

        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def _tool_function_video_generator(self, prompt: str, 
                                          negative_prompt: str = "Distorted, blurry, low quality, bad quality, low resolution, low detail, bad lighting, bad composition, bad framing, bad colors, bad contrast, bad saturation, bad sharpness", 
                                          enable_audio: bool = True, 
                                          audio_negative_prompt: str = "creepy, noisy, static, distorted, low quality, nonsensical", 
                                          duration: int = 5):
        # Validate parameters
        if duration < 5 or duration > 8:
            raise ValueError("Duration must be between 5 and 8 seconds")
    
        # Import
        _gradio_client = importlib.import_module("gradio_client")

        # Client
        _client = _gradio_client.Client("ginigen/VEO3-Directors")
        
        _result = await asyncio.to_thread(
            _client.predict,
            prompt=prompt,
            nag_negative_prompt=negative_prompt,
            nag_scale=11,
            height=1024,
            width=1024,
            duration_seconds=duration,
            steps=4,
            seed=2025,
            randomize_seed=True,
            enable_audio=enable_audio,
            audio_negative_prompt=audio_negative_prompt,
            audio_steps=25,
            audio_cfg_strength=4.5,
            api_name="/generate_video_with_audio"
        )

        print(_result)

        # Send the audio
        await self.method_send(file=discord.File(fp=_result["video"]))

        # Cleanup
        await aiofiles.os.remove(_result)
        return "Video generation success"