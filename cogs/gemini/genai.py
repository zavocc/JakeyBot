from core.ai.assistants import Assistants
from core.ai.models.gemini import Gemini
from discord.ext import commands
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from os import environ, remove
from pathlib import Path
import google.generativeai as genai
import google.api_core.exceptions #import PermissionDenied, InternalServerError
import aiohttp
import aiofiles
import asyncio
import discord
import inspect
import random
import yaml

# Load the models list from YAML file
with open("data/models.yaml", "r") as models:
    _internal_model_data = yaml.safe_load(models)

# Iterate through the models and merge them as dictionary
# It has to be put here instead of the init class since decorators doesn't seem to reference self class attributes
_model_choices = [
    discord.OptionChoice(f"{model['name']} - {model['description']}", model['model'])
    for model in _internal_model_data['gemini_models']
]

del _internal_model_data

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

    ###############################################
    # Ask command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @commands.cooldown(3, 6, commands.BucketType.user) # Add cooldown so GenerativeLanguage API won't hit rate limits in one's Google cloud account.
    @discord.option(
        "prompt",
        description="Enter your prompt, ask real questions, or provide a context for the model to generate a response",
        max_length=4096,
        required=True
    )
    @discord.option(
        "attachment",
        description="Attach your files to answer from. Supports image, audio, video, text, and PDF files",
        required=False,
    )
    @discord.option(
        "model",
        description="Choose a model to use for the conversation - flash is the default model",
        choices=_model_choices,
        default="gemini-1.5-flash-001",
        required=False
    )
    #@discord.option(
    #    "json_mode",
    #    description="Configures the response whether to format it in JSON",
    #    default=False,
    #)
    #@discord.option(
    #    "append_history",
    #    description="Store the conversation to chat history? (This option is void with json_mode)",
    #    default=True
    #)
    async def ask(self, ctx, prompt: str, attachment: discord.Attachment, model: str):
        """Ask a question using Gemini-based AI"""
        await ctx.response.defer()

        ###############################################
        # Model configuration
        ###############################################
        # Check for gemini API keys
        if environ.get("GOOGLE_AI_TOKEN") is None or environ.get("GOOGLE_AI_TOKEN") == "INSERT_API_KEY":
            raise Exception("GOOGLE_AI_TOKEN is not configured in the dev.env file. Please configure it and try again.")

        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

        # Message history
        # Since pycord 2.6, user apps support is implemented. But in order for this command to work in DMs, it has to be installed as user app
        # Which also exposes the command to the guilds the user joined where the bot is not authorized to send commands. This can cause partial function succession with MissingAccess error
        # One way to check is to check required permissions through @command.has_permissions(send_messages=True) or ctx.interaction.authorizing_integration_owners
        # The former returns "# This raises ClientException: Parent channel not found when ran outside of authorized guilds or DMs" which should be a good basis

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id # Always fallback to ctx.author.id for DMs since ctx.guild is None
        else:
            guild_id = ctx.author.id

        # This command is available in DMs
        if ctx.guild is not None:
            # This returns None if the bot is not installed or authorized in guilds
            # https://docs.pycord.dev/en/stable/api/models.html#discord.AuthorizingIntegrationOwners
            if ctx.interaction.authorizing_integration_owners.guild == None:
                await ctx.respond("🚫 This commmand can only be used in DMs or authorized guilds!")
                return

        # default system prompt - load assistants
        assistants_system_prompt = Assistants()
            
        # Model configuration 
        client = Gemini(bot=self.bot, ctx=ctx, model_name=model, 
                             system_prompt=assistants_system_prompt.jakey_system_prompt)

        ###############################################
        # File attachment processing
        ###############################################
        _xfile_uri = None
        # Enable multimodal support if an attachment is provided
        if attachment is not None:
            # Download the attachment
            _xfilename = f"{environ.get('TEMP_DIR')}/JAKEY.{guild_id}.{random.randint(5000, 6000)}.{attachment.filename}"
            try:
                async with aiohttp.ClientSession(raise_for_status=True) as session:
                    async with session.get(attachment.url, allow_redirects=True) as _xattachments:
                        # write to file with random number ID
                        async with aiofiles.open(_xfilename, "wb") as filepath:
                            async for _chunk in _xattachments.content.iter_chunked(8192):
                                await filepath.write(_chunk)
            except aiohttp.ClientError as httperror:
                # Remove the file if it exists ensuring no data persists even on failure
                if Path(_xfilename).exists():
                    remove(_xfilename)
                # Raise exception
                raise httperror

            # Upload the file to the Files API
            _xfile_uri = await client.multimodal_handler(attachment=Path(_xfilename), filename=attachment.filename)

            # Remove the file from the temp directory
            remove(_xfilename)

        ###############################################
        # Answer generation
        ###############################################
        _answer = await client.chat_completion(prompt, file=(_xfile_uri if _xfile_uri is not None else None))
    
        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_answer) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            with open(response_file, "w+") as f:
                f.write(_answer)
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"))
        elif len(_answer) > 2000:
            embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(prompt)[0:100],
                description=str(_answer),
                color=discord.Color.random()
            )
            embed.set_author(name=self.author)
            embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(_answer)

    # Handle all unhandled exceptions through error event, handled exceptions are currently image analysis safety settings
    @ask.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        # Cooldown error
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
            return

        # Check for safety or blocked prompt errors
        _exceptions = [genai.types.BlockedPromptException, genai.types.StopCandidateException, ValueError]

        # Get original exception from the DiscordException.original attribute
        error = getattr(error, "original", error)
        if any(_iter for _iter in _exceptions if isinstance(error, _iter)):
            await ctx.respond("❌ Sorry, I can't answer that question! Please try asking another question.")
        # Check if the error is InternalServerError
        elif isinstance(error, google.api_core.exceptions.InternalServerError):
            await ctx.respond("⚠️ Something went wrong (500) and its not your fault but its mostly you! If that's the case, please retry or try changing the model or rewrite your prompt.")
        # For failed downloads from attachments
        elif isinstance(error, aiohttp.ClientError):
            await ctx.respond("⚠️ Uh oh! Something went wrong while processing file attachment! Please try again later.")
        else:
            await ctx.respond(f"⚠️ Uh oh! I couldn't answer your question, something happend to our end!\nHere is the logs for reference and troubleshooting:\n ```{error}```")
        
        # Raise error
        raise error

def setup(bot):
    bot.add_cog(AI(bot))
