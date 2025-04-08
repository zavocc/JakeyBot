from os import environ
import aiohttp
import discord
import io

class Tool:
    tool_human_name = "Text to Speech"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "audio_generator",
                "description": "Generate audio from text",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {
                            "type": "STRING"
                        },
                        "voice": {
                            "type": "STRING",
                            "enum": [
                                "Aaliyah", "Adelaide", "Angelo", "Arista", "Atlas", "Basil", "Briggs", "Calum", "Celeste",
                                "Cheyenne", "Chip", "Cillian", "Deedee", "Eleanor", "Fritz", "Gail", "Indigo", "Jennifer",
                                "Judy", "Mamaw", "Mason", "Mikail", "Mitch", "Nia", "Quinn", "Ruby", "Thunder"
                            ]
                        }
                    },
                    "required": ["text"]
                }
            }
        ]

    # Audio generator using PlayHT Groq Voices
    async def _tool_function(self, text: str, voice: str = "Atlas"):
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