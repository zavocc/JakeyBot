from os import environ
import aiohttp
import discord
import inspect
import io

# Function implementations
class Tool:
    tool_human_name = "Image and audio generator"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "image_generator",
                "description": "Generate or restyle images using natural language or from description using Stable Diffusion 3.5",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_description": {
                            "type": "STRING"
                        }
                    },
                    "required": ["image_description"]
                }
            },
            {
                "name": "audio_generator",
                "description": "Generate audio from text using Azure Text-to-Speech",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {
                            "type": "STRING"
                        },
                        "voice": {
                            "type": "STRING",
                            "enum": [
                                "MALE",
                                "FEMALE",
                                "CUTE"
                            ]
                        }
                    },
                    "required": ["text", "voice"]
                }
            }
        ]

    # Image generator
    async def _tool_function_image_generator(self, image_description: str):
        # Check if HF_TOKEN is set
        if not environ.get("HF_TOKEN"):
            raise ValueError("HuggingFace API token is not set, please set it in the environment variables")

        # Create image
        message_curent = await self.method_send(f"⌛ Generating **{image_description}**... this may take few minutes")
        
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Payload
        _payload = {
            "inputs": image_description,
        }

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {environ.get('HF_TOKEN')}"
        }

        # Make a request
        async with _client_session.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo", json=_payload, headers=_headers) as _response:
            # Check if the response is not 200 which may print JSON
            # Response 200 would return the binary image
            if _response.status != 200:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Send the image
            _imagedata = await _response.content.read()

        # Delete status
        await message_curent.delete()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_imagedata), filename="generated_image.png"))

        # Cleanup
        return "Image generation success and the file should be sent automatically"

    # Audio generator using Azure Text-to-Speech
    async def _tool_function_audio_generator(self, text: str, voice: str):
        # Check if AZURE_TTS_KEY is set
        if not environ.get("AZURE_TTS_KEY"):
            raise ValueError("Azure TTS API key is not set, please set it in the environment variables")

        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Check if AZURE_TTS_REGION is set if not, assume its eastus
        if not environ.get("AZURE_TTS_REGION"):
            environ["AZURE_TTS_REGION"] = "eastus"

        _headers = {
            "Ocp-Apim-Subscription-Key": environ.get("AZURE_TTS_KEY"),
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-160kbitrate-mono-mp3"
        }

        # Check for voices
        # MALE = en-US-DerekMultilingualNeural
        # FEMAILE = en-US-JennyNeural
        # CUTE = en-US-AnaNeural
        if voice == "MALE":
            _voiceType = "en-US-DerekMultilingualNeural"
            _voiceGender = "Male"
        elif voice == "FEMALE":
            _voiceType = "en-US-JennyNeural"
            _voiceGender = "Female"
        elif voice == "CUTE":
            _voiceType = "en-US-AnaNeural"
            _voiceGender = "Female"

        _xmlData = inspect.cleandoc(rf"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                <voice xml:gender='{_voiceGender}' name='{_voiceType}'>
                    {text}
                </voice>
            </speak>""")

        # Make a request
        async with _client_session.post(f"https://{environ["AZURE_TTS_REGION"]}.tts.speech.microsoft.com/cognitiveservices/v1", data=_xmlData, headers=_headers) as _response:
            if _response.status != 200:
                raise Exception(f"Failed to generate audio with code {_response.status}, reason: {_response.reason}")
            
            # Ensure the output is audio and in binary format
            if not "audio" in _response.headers["Content-Type"]:
                raise Exception("The response from the Azure TTS API is not in audio format")

            # Send the audio
            _audio = await _response.content.read()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_audio), filename="voice.mp3"))

        # Cleanup
        return "Audio success and the file should be sent automatically"