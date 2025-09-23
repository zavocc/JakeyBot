from cogs.ai.generative_chat import BaseChat
from core.database import History
from core.exceptions import *
from discord.commands import SlashCommandGroup
from discord.ext import commands
from models.chat_utils import fetch_model
from os import environ
from tools.utils import fetch_actual_tool_name
import discord
import logging
import models.core

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Initialize the MongoDB connection and History management
        try:
            self.DBConn: History = History(
                bot=bot,
                conn_string=environ.get("MONGO_DB_URL")
            )
        except Exception as e:
            raise e(f"Failed to connect to MongoDB: {e}...\n\nPlease set MONGO_DB_URL in dev.env")

        # Initialize the chat system
        self._ask_event = BaseChat(bot, self.author, self.DBConn)

    #######################################################
    # Pending request checker, prevents running multiple requests concurrently
    #######################################################
    async def _check_awaiting_response_in_progress(self, user_id: int):
        if user_id in self._ask_event.pending_ids:
            raise ConcurrentRequestError

    #######################################################
    # Event Listener: on_message
    #######################################################
    @commands.Cog.listener()
    async def on_message(self, message):
        await self._ask_event.on_message(message)

    #######################################################
    # Model Slash Command Group
    model = SlashCommandGroup(name="model", description="Configure default models for the conversation")

    #######################################################
    # Slash Command Group: model.set
    #######################################################
    @model.command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option(
        "model",
        description="Choose default model for the conversation",
        choices=models.core.get_models_generator(),
        required=True,
    )
    async def set(self, ctx, model: str):
        """Set the default model whenever you mention me!"""
        await ctx.response.defer(ephemeral=True)

        # Check if inference is in progress
        await self._check_awaiting_response_in_progress(ctx.author.id)

        # Save the default model in the database
        # await self.DBConn.set_default_model(guild_id=ctx.author.id, model=model)
        await self.DBConn.set_key(guild_id=ctx.author.id, key="default_model", value=model)

        # Validate model
        _model_props = await fetch_model(model_alias=model)

        # Chat thread
        if _model_props.thread_name:
            _thread_name = _model_props.thread_name
        else:
            _thread_name = _model_props.sdk

        _strings = f"✅ Default model set to **{_model_props.model_human_name}** and chat thread is assigned to **{_thread_name}**"
        if not _model_props.enable_tools:
            await ctx.respond(f"> This model lacks real time information and tools\n" + _strings)
        else:
            await ctx.respond(_strings)


    #######################################################
    # Slash Command: openrouter
    #######################################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option(
        "model",
        description="Choose models at https://openrouter.ai/models. Syntax: provider/model-name",
        required=True,
    )
    async def openrouter(self, ctx, model: str):
        """Set the default OpenRouter model"""
        await ctx.response.defer(ephemeral=True)

        # Check if inference is in progress
        await self._check_awaiting_response_in_progress(ctx.author.id)

        # Set the default OpenRouter model and clear the OpenRouter chat thread
        await self.DBConn.set_key(guild_id=ctx.author.id, key="default_openrouter_model", value=model)
        _setkeymodel = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_openrouter_model")

        # Clear ongoing conversations
        await self.DBConn.set_key(guild_id=ctx.author.id, key="chat_thread_openrouter", value=None)

        # Respond
        await ctx.respond(
            f"✅ Default OpenRouter model set to **{_setkeymodel}** and chat history for OpenRouter chats are cleared!\n"
            "To use this model, please set the model to OpenRouter using `/model set` command"
        )

    #######################################################
    # Slash Command: sweep
    #######################################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option(
        "reset_prefs",
        description="Clear the context history including the default model and feature settings",
    )
    async def sweep(self, ctx, reset_prefs: bool = False):
        """Clear the context history of the conversation"""
        await ctx.response.defer(ephemeral=True)

        # Check if inference is in progress
        await self._check_awaiting_response_in_progress(ctx.author.id)

        # Command allowed only in DMs or in authorized guilds
        if ctx.guild is not None:
            if ctx.interaction.authorizing_integration_owners.guild is None:
                await ctx.respond("🚫 This command can only be used in DMs or authorized guilds!")
                return

        # Save current settings before clearing history
        _feature = await self.DBConn.get_key(guild_id=ctx.author.id, key="tool_use")
        _model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_model")
        _openrouter_model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_openrouter_model")

        # Clear chat history
        await self.DBConn.clear_history(guild_id=ctx.author.id)

        if not reset_prefs:
            # Restore settings if not resetting preferences
            await self.DBConn.set_key(guild_id=ctx.author.id, key="tool_use", value=_feature)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_model", value=_model)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_openrouter_model", value=_openrouter_model)
            await ctx.respond("✅ Chat history reset!")
        else:
            await ctx.respond("✅ Chat history reset, model and feature settings are cleared!")



    #######################################################
    # Slash Command: agent
    #######################################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option(
        "agent_name",
        description="Integrate tools to chat! Setting chat agents will clear your history!",
        choices=models.core.get_tools_list_generator(),
    )
    async def agent(self, ctx, agent_name: str):
        """Connect chat with tools to perform tasks, such as searching the web, generate images, and more."""
        await ctx.response.defer(ephemeral=True)

        # Check if inference is in progress
        await self._check_awaiting_response_in_progress(ctx.author.id)

        # Command allowed only in DMs or in authorized guilds
        if ctx.guild is not None:
            if ctx.interaction.authorizing_integration_owners.guild is None:
                await ctx.respond("🚫 This command can only be used in DMs or authorized guilds!")
                return

        # Retrieve current settings
        _current_agent = await self.DBConn.get_key(guild_id=ctx.author.id, key="tool_use")
        _model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_model")
        _openrouter_model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_openrouter_model")

        # Convert "disabled" to None
        if agent_name == "disabled":
            agent_name = None

        if _current_agent == agent_name:
            await ctx.respond("✅ Agent already set!")
        else:
            # Clear chat history IF the agent is not set to None
            if _current_agent:
                await self.DBConn.clear_history(guild_id=ctx.author.id)

            # Set new agent_name and restore default model
            await self.DBConn.set_key(guild_id=ctx.author.id, key="tool_use", value=agent_name)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_model", value=_model)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_openrouter_model", value=_openrouter_model)

            if agent_name is None:
                await ctx.respond("✅ Features disabled and chat is reset to reflect the changes")
            else:
                # Return with actual tool name
                _actual_human_agent_name = await fetch_actual_tool_name(agent_name)

                if not _current_agent:
                    await ctx.respond(f"✅ Feature **{_actual_human_agent_name}** enabled successfully")
                else:
                    await ctx.respond(f"✅ Feature **{_actual_human_agent_name}** enabled successfully and chat is reset to reflect the changes")

    # Global error handler for the Cog
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        _error = getattr(error, "original", error)
        
        if isinstance(_error, ConcurrentRequestError):
            await ctx.reply("⚠️ Please wait until processing your previous request is completed...")
        elif isinstance(_error, CustomErrorMessage):
            await ctx.reply(_error.message)
        elif isinstance(_error, PermissionError):
            await ctx.reply("⚠️ An error has occurred while clearing chat history, logged the error to the owner")
        elif isinstance(_error, FileNotFoundError):
            await ctx.reply("ℹ️ Chat history is already cleared!")
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.reply("Sorry, you can only use this in private messages!")
        else:
            await ctx.reply("❌ Something went wrong, please try again later.")
            logging.error("An error has occurred while executing command, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(Chat(bot))
