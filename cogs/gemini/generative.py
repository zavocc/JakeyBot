from core.ai.assistants import Assistants
from core.ai.core import ModelsList
from core.ai.history import History
from discord.ext import commands
from os import environ, remove
import google.generativeai as genai
import google.api_core.exceptions
import core.ai.models.gemini.infer
import aiohttp
import aiofiles
import aiofiles.os
import discord
import importlib
import inspect
import motor.motor_asyncio
import random

class BaseChat(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Load the database and initialize the HistoryManagement class
        # MongoDB database connection for chat history and possibly for other things
        try:
            self.DBConn: History = History(db_conn=motor.motor_asyncio.AsyncIOMotorClient(environ.get("MONGO_DB_URL")))
        except Exception as e:
            raise e(f"Failed to connect to MongoDB: {e}...\n\nPlease set MONGO_DB_URL in dev.env")

        # Check for gemini API keys
        if environ.get("GOOGLE_AI_TOKEN") is None or environ.get("GOOGLE_AI_TOKEN") == "INSERT_API_KEY":
            raise Exception("GOOGLE_AI_TOKEN is not configured in the dev.env file. Please configure it and try again.")
        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

        # default system prompt - load assistants
        self._assistants_system_prompt = Assistants()

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
        choices=ModelsList.get_models_list(),
        default="__gemini__gemini-1.5-flash-002",
        required=False
    )
    @discord.option(
        "append_history",
        description="Store the conversation to chat history?",
        default=True
    )
    @discord.option(
        "verbose_logs",
        description="Show logs, context usage, and model information",
        default=False
    )
    async def ask(self, ctx, prompt: str, attachment: discord.Attachment, model: str,
        append_history: bool, verbose_logs: bool):
        """Ask a question using Gemini-based AI"""
        await ctx.response.defer()

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

        # Configure infer
        _model = model.split("__")
        _infer: core.ai.models.gemini.infer.Completions = importlib.import_module(f"core.ai.models.{_model[1]}.infer").Completions(
            guild_id=guild_id,
            model={"model_provider": _model[1], "model_name": _model[-1]},
            db_conn = self.DBConn,
            _discord_bot=self.bot,
            _discord_ctx=ctx
        )

        ###############################################
        # File attachment processing
        ###############################################
        if attachment is not None:
            await _infer.multimodal_setup(attachment=attachment, verbose_logs=verbose_logs)

        ###############################################
        # Answer generation
        ###############################################
        _result = await _infer.completion(prompt=prompt, system_instruction=self._assistants_system_prompt.jakey_system_prompt)
    
        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_result["answer"]) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            async with aiofiles.open(response_file, "w+") as f:
                await f.write(_result["answer"])
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"))
        elif len(_result["answer"]) > 2000:
            embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(prompt)[0:100],
                description=str(_result["answer"]),
                color=discord.Color.random()
            )
            embed.set_author(name=self.author)
            embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(_result["answer"])

        # Print context size and model info
        if append_history:
            await _infer.save_to_history(chat_thread=_result["chat_thread"], prompt_count=_result["prompt_count"])
            if verbose_logs:
                await ctx.send(inspect.cleandoc(f"""
                            > 📃 Context size: **{_result["prompt_count"]}** of {environ.get("MAX_CONTEXT_HISTORY", 20)}
                            > ✨ Model used: **{_model[-1]}**
                            """))
        else:
            if verbose_logs:
                await ctx.send(f"> 📃 Responses isn't be saved\n> ✨ Model used: **{model[-1]}**")

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
        elif isinstance(error, ModuleNotFoundError):
            await ctx.respond("⚠️ Uh oh! The tool is not available at the moment at our side, please try again later or change tools using `/feature`.")
        elif isinstance(error, MemoryError):
            await ctx.respond("📝 Sorry, the chat thread has reached its maximum capacity, please clear the chat history to continue using `/sweep`")
        else:
            await ctx.respond(f"⚠️ Uh oh! I couldn't answer your question, something happend to our end!\nHere is the logs for reference and troubleshooting:\n ```{error}```")
        
        # Raise error
        raise error