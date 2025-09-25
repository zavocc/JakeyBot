from models.tasks.media.fal_ai import run_audio
from os import environ
import aiohttp
import datetime
import discord
import filetype
import io
import logging

# Function implementations
class Tools:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Audio generator
    async def tool_text_to_speech(self, text: str, voice: str = "Brian", style: float = 0.5):
        # Create audio       
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Audio Generation tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.info("No aiohttp instance found in discord bot subclass, creating a new one for Audio Generation tool")
            _aiohttp_client_session = aiohttp.ClientSession()

        # Generate audio
        _discordAudioURLs = []
        _audiosInBytes = await run_audio(
            model_name="elevenlabs/tts/eleven-v3",
            aiohttp_session=_aiohttp_client_session,
            text=text,
            voice=voice,
            style=style
        )

        # Send the audio and add each of the discord message to the list so we can add it as context later
        for _index, _audios in enumerate(_audiosInBytes):
            # Check the audio type
            _magicType = filetype.guess(_audios)
            if _magicType.mime == "audio/mpeg":
                _formatExtension = "mp3"
            elif _magicType.mime == "audio/wav":
                _formatExtension = "wav"
            elif _magicType.mime == "audio/ogg":
                _formatExtension = "ogg"
            else:
                _formatExtension = "bin"

            # Filename
            _fileName = f"generated_speech_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{_index}.{_formatExtension}"

            _sentAud = await self.discord_ctx.channel.send(file=discord.File(io.BytesIO(_audios), filename=_fileName))
            _discordAudioURLs.append(_sentAud.attachments[0].url)


        # Delete the _audiosInBytes to save memory
        del _audiosInBytes

         # Cleanup
        return "The audio is already sent to the UI, no need to print the URLs again as it will just cause previews to display audio twice.",


    # Music gen
    async def tool_music_generator(self, prompt: str, duration: int = 60):
        # If exceeding 190 seconds, cap it to 190s
        if duration > 190:
            duration = 190

        # Send an embed featuring a banner that Jakey can now generate music
        _music_banner = discord.Embed(
            title="Jakey is now generating a music for you",
            color=discord.Color.purple(),
        )
        _music_banner.add_field(name="Prompt", value=prompt, inline=False)
        _music_banner.add_field(name="Duration", value=f"{duration} seconds", inline=False)
        _music_banner.set_footer(text="Powered by Stable Audio 2.5 provided by FAL")
        _music_banner.set_image(url="https://media.discordapp.net/attachments/1267742831062159370/1419625685328203838/tunesnanobanana.png")

        _embedInterstMsg = await self.discord_ctx.channel.send(embed=_music_banner)

        # Generate audio
        _audiosInURL = await run_audio(
            model_name="stable-audio-25/text-to-audio",
            send_url_only=True,
            prompt=prompt,
            seconds_total=duration
        )

        # Edit the banner to indicate completion
        _music_banner.color = discord.Color.green()
        _music_banner.title = "You can now download your generated music from the link below"
        _music_banner.description = f"[Download your music here]({_audiosInURL})"
        _music_banner.set_image(url=None)
        await _embedInterstMsg.edit(embed=_music_banner)

        # Send the audio
        return f"Tell the user the audio is ready to [Download]({_audiosInURL})",

    # Podcast generator
    async def tool_podcastgen(self, dialogues: list[dict], enable_background_music: bool = False):
        # Create audio       
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp instance from discord bot subclass for Podcast Generation tool")
            _aiohttp_client_session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance
        else:
            logging.info("No aiohttp instance found in discord bot subclass, creating a new one for Podcast Generation tool")
            _aiohttp_client_session = aiohttp.ClientSession()

        # Construct the dialogue script
        _structured_script = ""
        for _dialogue in dialogues:
            _structured_script += f"{_dialogue['speaker_type']}: {_dialogue['dialogue']}\n"

        # Generate audio
        _discordAudioURLs = []
        _audiosInBytes = await run_audio(
            model_name="vibevoice/7b",
            aiohttp_session=_aiohttp_client_session,
            script=_structured_script,
            speakers=[
                {
                    "preset": "Frank [EN]",
                },
                {
                    "preset": "Mary [EN] (Background Music)" if enable_background_music else "Maya [EN]",
                }
            ]
        )

        # Send the audio and add each of the discord message to the list so we can add it as context later
        for _index, _audios in enumerate(_audiosInBytes):
            # Check the audio type
            _magicType = filetype.guess(_audios)
            if _magicType.mime == "audio/mpeg":
                _formatExtension = "mp3"
            elif _magicType.mime == "audio/wav":
                _formatExtension = "wav"
            elif _magicType.mime == "audio/ogg":
                _formatExtension = "ogg"
            else:
                _formatExtension = "bin"

            # Filename
            _fileName = f"generated_speech_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{_index}.{_formatExtension}"

            _sentAud = await self.discord_ctx.channel.send(file=discord.File(io.BytesIO(_audios), filename=_fileName))
            _discordAudioURLs.append(_sentAud.attachments[0].url)


        # Delete the _audiosInBytes to save memory
        del _audiosInBytes

         # Cleanup
        return "The audio is already sent to the UI, no need to print the URLs again as it will just cause previews to display audio twice.",
