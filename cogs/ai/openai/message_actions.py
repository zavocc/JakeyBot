from core.ai.models.openai.infer import Completions
from core.ai.assistants import Assistants
from discord.ext import commands
from os import environ
import discord
import aiofiles
import random

class GenAIApps_OpenAI(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Assistants
        self._system_prompt = Assistants()

    ###############################################
    # Rephrase command
    ###############################################
    @commands.message_command(
        name="Speak this message",
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install},
    )
    async def speakmsg(self, ctx, message: discord.Message):
        """Rephrase this message"""
        await ctx.response.defer(ephemeral=True)
        
        # Generative model settings
        _completion = Completions()
        _audiodata = await _completion.audio_completion(f"Can you speak this message but add tone and emotion based on the message content:\n{str(message.content)}")

        # Save it to file
        _filepth = f"{environ.get('TEMP_DIR')}/JAKEY_GPT4o_AUDIOWOLOLO_{random.randint(22831,96482)}.wav"
        async with aiofiles.open(_filepth, "wb") as _file:
            await _file.write(_audiodata)

        await ctx.respond("Here is the spoken message:", file=discord.File(_filepth, filename=f"{message.content[:15]}.wav"))
        await aiofiles.os.remove(_filepth)

    @speakmsg.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        _error = getattr(error, "original", error)
        if isinstance(_error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
        elif isinstance(_error, ModuleNotFoundError):
            await ctx.respond("❌ Sorry, I don't have the capability to do this yet.")
        else:
            await ctx.respond("❌ Sorry, I couldn't speak that message. I'm still learning!")
        raise error

def setup(bot):
    bot.add_cog(GenAIApps_OpenAI(bot))
