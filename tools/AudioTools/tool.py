from .manifest import ToolManifest
from core.services.helperfunctions import HelperFunctions
from os import environ
import aiofiles.os
import aiohttp
import asyncio
import datetime
import discord
import google.genai as genai
import importlib
import io
import wave

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
    
    async def _tool_function_audio_generator_gemini(self, text: str, style: str = None, voice: str = "Puck"):
        # Check if global aiohttp and google genai client session is initialized
        if not hasattr(self.discord_bot, "_gemini_api_client"):
            raise Exception("gemini api client isn't set up, please check the bot configuration")
        
        _api_client: genai.Client = self.discord_bot._gemini_api_client

        # prompt
        _prompt = ["Text to be read:", text]
        _prompt.append(f"Please generate the audio and read the text given above in {style} style") if style else "Read the text given above"

        # Generate response
        _response = await _api_client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents="\n".join(_prompt),
            config={
                "response_modalities": ["Audio"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice
                        }
                    }
                }
            }
        )


        # Send the audio
        for _parts in _response.candidates[0].content.parts:
            if _parts.inline_data and _parts.inline_data.data:
                # Use wave to correctly write wave data as bytes
                _wav_buffer = io.BytesIO()
                with wave.open(_wav_buffer, "wb") as _audio_file:
                    _audio_file.setnchannels(1)
                    _audio_file.setsampwidth(2)
                    _audio_file.setframerate(24000)
                    _audio_file.writeframes(_parts.inline_data.data)
                _wav_buffer.seek(0)

                 # Send the audio
                _audioSent = await self.method_send(file=discord.File(fp=_wav_buffer, filename=f"generated_audio.wav"))

        if _audioSent:
            return "Audio success and the file is sent automatically"
        else:
            raise Exception("The response from Gemini is not in audio format")
        
    async def _tool_function_podcastgen(self, dialogues: dict, intent: str, est_listening_time, brief_premise):
        # Check if global aiohttp and google genai client session is initialized
        if not hasattr(self.discord_bot, "_gemini_api_client"):
            raise Exception("gemini api client isn't set up, please check the bot configuration")
        
        # Check for Azure blob storage client
        if not hasattr(self.discord_bot, "_azure_blob_service_client"):
            raise Exception("Azure blob storage client isn't set up, please check the bot configuration")
        
        # Check API client
        _api_client: genai.Client = self.discord_bot._gemini_api_client

        await self.method_send(f"🎙️Generating podcast with intent: **{intent}**")
        await self.method_send(f"⏳Estimated listening time: **{est_listening_time}**")
        await self.method_send(f"📜Premise: **{brief_premise}**")

        # Construct the prompt from dialogues
        # "dialogues":{
        #     "speaker_type": str,
        #     "dialogue": str
        # }
        _prompt = [
            "Generate a podcast script based on the following dialogues:",
            "Make sure to add emotions, laughs, and pauses to make it sound natural especially when interesting excerpts came like funny quotes.",
            "The voice must be interesting, curious, engaging, and entertaining."
        ]
        for _dialogue in dialogues:
            if _dialogue["speaker_type"] == "host_one":
                _prompt.append(f"Host 1: { _dialogue['dialogue'] }")
            elif _dialogue["speaker_type"] == "host_two":
                _prompt.append(f"Host 2: { _dialogue['dialogue'] }")

        # Generate response
        _response = await _api_client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents="\n".join(_prompt),
            config={
                "response_modalities": ["Audio"],
                "speech_config": {
                    "multi_speaker_voice_config": {
                        "speaker_voice_configs": [
                            {
                                "speaker": "Host 1",
                                "voice_config": {
                                    "prebuilt_voice_config": {
                                        "voice_name": "Iapetus"
                                    }
                                }
                            },
                            {
                                "speaker": "Host 2",
                                "voice_config": {
                                    "prebuilt_voice_config": {
                                        "voice_name": "Autonoe"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        )

        # Filename for the podcast
        _podcast_filename = f"podcast-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.wav"
        _podcast_url = None

        # Send the audio
        for _parts in _response.candidates[0].content.parts:
            if _parts.inline_data and _parts.inline_data.data:
                # Use wave to correctly write wave data as bytes
                _wav_buffer = io.BytesIO()
                with wave.open(_wav_buffer, "wb") as _audio_file:
                    _audio_file.setnchannels(1)
                    _audio_file.setsampwidth(2)
                    _audio_file.setframerate(24000)
                    _audio_file.writeframes(_parts.inline_data.data)
                _wav_buffer.seek(0)

                # Send the audio
                try:
                    _podcast_url = await HelperFunctions.upload_file_service(
                        bot=self.discord_bot,
                        filename=_podcast_filename,
                        data=_wav_buffer.getvalue()
                    )
                except Exception as e:
                    raise Exception(f"Failed to upload podcast audio")

        # Get the URL of the podcast
        return f"Podcast generation success, remind the user to download the file as [Download here]({_podcast_url}) as this hosted audio will expire in two days"

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

