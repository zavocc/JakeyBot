from core.ai.core import ModelsList
from cogs.ai.generative import BaseChat
from cogs.ai.generative_event import BaseChat as BaseChatEvent
from core.ai.history import History
from core.exceptions import GeminiClientRequestError, ModelUnavailable, MultiModalUnavailable, ToolsUnavailable
from discord.commands import SlashCommandGroup
from discord.ext import commands
from os import environ
import aiofiles.ospath
import discord
import inspect
import logging
import motor.motor_asyncio

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Load the database and initialize the HistoryManagement class
        # MongoDB database connection for chat history and possibly for other things
        try:
            self.DBConn: History = History(db_conn=motor.motor_asyncio.AsyncIOMotorClient(environ.get("MONGO_DB_URL")))
        except Exception as e:
            raise e(f"Failed to connect to MongoDB: {e}...\n\nPlease set MONGO_DB_URL in dev.env")

        # Initialize the chat system
        self._ask_command = BaseChat(bot, self.author, self.DBConn)
        self._ask_event = BaseChatEvent(bot, self.author, self.DBConn)

    ###############################################
    # Ask event slash command
    ###############################################
    @commands.Cog.listener()
    async def on_message(self, message):
        await self._ask_event.on_message(message)

    ###############################################
    # Ask slash command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @commands.cooldown(3, 6, commands.BucketType.user) # Add cooldown to prevent abuse
    @discord.option(
        "prompt",
        input_type=str,
        description="Enter your prompt, ask real questions, or provide a context for the model to generate a response",
        max_length=4096,
        required=True
    )
    @discord.option(
        "attachment",
        input_type=discord.Attachment,
        description="Attach your files to answer from. Supports image, audio, video, text, and PDF files",
        required=False,
    )
    @discord.option(
        "model",
        input_type=str,
        description="Choose a model to use for the conversation - flash is the default model",
        choices=ModelsList.get_models_list(),
        default="gemini::gemini-1.5-flash-002",
        required=False
    )
    @discord.option(
        "append_history",
        input_type=bool,
        description="Store the conversation to chat history?",
        default=True
    )
    @discord.option(
        "show_info",
        input_type=bool,
        description="Show information about the model, tool, files used through an embed",
        default=False
    )
    async def ask(self, ctx, prompt, attachment, model, append_history, show_info):
        """Ask a question using Gemini and models from OpenAI, Anthropic, and more!"""
        await self._ask_command.ask(ctx, prompt, attachment, model, append_history, show_info)

    @ask.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        _error = getattr(error, "original", error)
        # Cooldown error
        if isinstance(_error, commands.CommandOnCooldown):
            await ctx.respond(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
        elif isinstance(_error, GeminiClientRequestError):
            await ctx.respond(f"😨 Uh oh, something happened to our end while processing requests code **{_error.error_code}** with reason: **{_error.error_message}**")
        elif isinstance(_error, MultiModalUnavailable):
            await ctx.respond("🚫 This model cannot process certain files, choose another model to continue")
        elif isinstance(_error, ModelUnavailable):
            await ctx.respond(f"⚠️ The model you've chosen is not available at the moment, please choose another model")
        elif isinstance(_error, ToolsUnavailable):
            await ctx.respond(f"⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
        else:
            logging.error("%s: An error has occured when Jakey is generating an answer, reason: %s", (await aiofiles.ospath.abspath(__file__)), _error)
            await ctx.respond(f"❌ Sorry, I couldn't answer your question at the moment, check console logs. What exactly happened: **`{type(_error).__name__}`**")

        # Raise error
        raise _error
    
    ###############################################
    # For /model slash command group
    ###############################################
    model = SlashCommandGroup(name="model", description="Configure default models for the conversation")

    ###############################################
    # Set default model command
    ###############################################
    @model.command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "model",
        description="Choose default model for the conversation",
        choices=ModelsList.get_models_list(),
        required=True
    )
    async def set(self, ctx, model: str):
        """Set the default model whenever you mention the me!"""
        await ctx.response.defer(ephemeral=False)

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        else:
            guild_id = ctx.author.id

        # Save the default model in the database
        await self.DBConn.set_default_model(guild_id=guild_id, model=model)

        # Split the model name to get the provider and model name
        # If it has :: prefix
        if "::" not in model:
            await ctx.respond("❌ Invalid model name, please choose a model from the list")
            return
        else:
            _model = model.split("::")
            _model_provider = _model[0]
            _model_name = _model[-1]

        await ctx.respond(f"✅ Default model set to **{_model_name}** and chat history is set for provider **{_model_provider}**")

    ###############################################
    # List models command
    ###############################################
    @model.command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    async def list(self, ctx):
        """List all available models"""
        await ctx.response.defer(ephemeral=True)

        # Create an embed
        _embed = discord.Embed(
            title="Available models",
            description=inspect.cleandoc(
                f"""Here are the list of available models that you can use

                You can set the default model for the conversation using `/model set` command or on demand through chat prompting
                via `@{self.bot.user.name} /model:model-name` command
                
                Each provider has its own chat history, skills, and capabilities. Choose what's best for you"""),
            color=discord.Color.random()
        )

        # Iterate over models
        # Now we separate model provider into field and model names into value
        # It is __provider__model-name so we need to split it and group them as per provider
        _model_provider_tabledict = {}

        async for _model in ModelsList.get_models_list_async():
            _model_provider = _model.split("::")[0]
            _model_name = _model.split("::")[-1]

            # Add the model name to the corresponding provider in the dictionary
            if _model_provider not in _model_provider_tabledict:
                _model_provider_tabledict[_model_provider] = [_model_name]
            else:
                _model_provider_tabledict[_model_provider].append(_model_name)

        # Add fields to the embed
        for provider, models in _model_provider_tabledict.items():
            _embed.add_field(name=provider, value=", ".join(models), inline=False)

        # Send the status
        await ctx.respond(embed=_embed)

    # Handle errors
    @model.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        await ctx.respond("❌ Something went wrong, please check the console logs for details.")
        raise error

    ###############################################
    # Clear context command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "reset_prefs",
        description="Clear the context history including the default model and feature settings",
    )
    async def sweep(self, ctx, reset_prefs: bool = False):
        """Clear the context history of the conversation"""
        await ctx.response.defer()

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        else:
            guild_id = ctx.author.id

        # This command is available in DMs
        if ctx.guild is not None:
            # This returns None if the bot is not installed or authorized in guilds
            # https://docs.pycord.dev/en/stable/api/models.html#discord.AuthorizingIntegrationOwners
            if ctx.interaction.authorizing_integration_owners.guild == None:
                await ctx.respond("🚫 This commmand can only be used in DMs or authorized guilds!")
                return  

        # Get current feature and model
        _feature = await self.DBConn.get_config(guild_id=guild_id)
        _model = await self.DBConn.get_default_model(guild_id=guild_id)

        print(_feature, _model)

        # Clear and set feature and model
        await self.DBConn.clear_history(guild_id=guild_id)

        if not reset_prefs:
            await self.DBConn.set_config(guild_id=guild_id, tool=_feature)
            await self.DBConn.set_default_model(guild_id=guild_id, model=_model)
            await ctx.respond("✅ Chat history reset!")
        else:
            await ctx.respond("✅ Chat history reset, model and feature settings are cleared!")

    # Handle errors
    @sweep.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        # Get original error
        _error = getattr(error, "original")
        if isinstance(_error, PermissionError):
            await ctx.respond("⚠️ An error has occured while clearing chat history, logged the error to the owner")
        elif isinstance(_error, FileNotFoundError):
            await ctx.respond("ℹ️ Chat history is already cleared!")
        else:
            await ctx.respond("❌ Something went wrong, please check the console logs for details.")
            raise error

    ###############################################
    # Set chat features command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "capability",
        description = "Integrate tools to chat! Setting chat features will clear your history!",
        choices=ModelsList.get_tools_list(),
    )
    async def feature(self, ctx, capability: str):
        """Enhance your chat with capabilities! Some are in BETA so things may not always pick up"""
        # Defer
        await ctx.response.defer()

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        else:
            guild_id = ctx.author.id

        # This command is available in DMs
        if ctx.guild is not None:
            # This returns None if the bot is not installed or authorized in guilds
            # https://docs.pycord.dev/en/stable/api/models.html#discord.AuthorizingIntegrationOwners
            if ctx.interaction.authorizing_integration_owners.guild == None:
                await ctx.respond("🚫 This commmand can only be used in DMs or authorized guilds!")
                return

        # if tool use is the same, do not clear history
        _feature = await self.DBConn.get_config(guild_id=guild_id)

        # Default model
        _model = await self.DBConn.get_default_model(guild_id=guild_id)

        print(_feature, _model)

        # Check default model
        if _feature == capability:
            await ctx.respond("✅ Feature already enabled!")
        else:
            # set config
            await self.DBConn.set_config(guild_id=guild_id, tool=capability)
            await self.DBConn.set_default_model(guild_id=guild_id, model=_model)
            await ctx.respond(f"✅ Feature **{capability}** enabled successfully and chat is reset to reflect the changes")

            print(_feature, _model)
        
    # Handle errors
    @feature.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        await ctx.respond("❌ Something went wrong, please check the console logs for details.")
        raise error

def setup(bot):
    bot.add_cog(Chat(bot))