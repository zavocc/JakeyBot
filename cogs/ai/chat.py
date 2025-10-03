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

        # Configure cooldown
        self._cooldown = commands.CooldownMapping.from_cooldown(2, 25, commands.BucketType.user)

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
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check cooldown
        _ubucket = self._cooldown.get_bucket(message)
        _rl_float_rate = _ubucket.update_rate_limit()
        if _rl_float_rate:
            await message.reply(f"⌛ Please wait for **{int(_rl_float_rate)}** seconds before sending another message...", mention_author=True, delete_after=5)
            return
        
        await self._ask_event.on_message(message)

    #######################################################
    # Checkpoint Slash Command Group
    checkpoint = SlashCommandGroup(name="checkpoint", description="Manage user data checkpoints")

    #######################################################
    # Slash Command: checkpoint save
    #######################################################
    @checkpoint.command(
        name="save",
        description="Save the current user data as a checkpoint.",
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option("name", description="The name for the checkpoint.", required=True)
    async def save(self, ctx, name: str):
        await ctx.response.defer(ephemeral=True)
        try:
            await self.DBConn.create_checkpoint(guild_id=ctx.author.id, name=name)
            await ctx.respond(f"✅ Checkpoint '{name}' saved successfully.")
        except HistoryDatabaseError as e:
            await ctx.respond(f"❌ {e}")
        except Exception as e:
            logging.error(f"Error saving checkpoint: {e}")
            await ctx.respond("❌ An error occurred while saving the checkpoint.")

    #######################################################
    # Slash Command: checkpoint list
    #######################################################
    @checkpoint.command(
        name="list",
        description="List all saved checkpoints.",
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    async def list_checkpoints(self, ctx):
        await ctx.response.defer(ephemeral=True)
        try:
            checkpoints = await self.DBConn.list_checkpoints(guild_id=ctx.author.id)
            if not checkpoints:
                await ctx.respond("No checkpoints found.")
                return

            embed = discord.Embed(title="Saved Checkpoints", color=discord.Color.blue())
            for cp in checkpoints:
                embed.add_field(name=cp['name'], value=f"Created: {cp['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}", inline=False)
            await ctx.respond(embed=embed)
        except Exception as e:
            logging.error(f"Error listing checkpoints: {e}")
            await ctx.respond("❌ An error occurred while listing checkpoints.")

    #######################################################
    # Autocomplete for checkpoint names
    #######################################################
    async def _checkpoint_autocomplete(self, ctx: discord.AutocompleteContext):
        checkpoints = await self.DBConn.list_checkpoints(guild_id=ctx.interaction.user.id)
        return [cp['name'] for cp in checkpoints if cp['name'].lower().startswith(ctx.value.lower())]

    #######################################################
    # Slash Command: checkpoint restore
    #######################################################
    @checkpoint.command(
        name="restore",
        description="Restore user data from a checkpoint.",
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option("name", description="The name of the checkpoint to restore.", required=True, autocomplete=discord.utils.basic_autocomplete(_checkpoint_autocomplete))
    async def restore(self, ctx, name: str):
        await ctx.response.defer(ephemeral=True)
        try:
            await self.DBConn.restore_checkpoint(guild_id=ctx.author.id, name=name)
            await ctx.respond(f"✅ Checkpoint '{name}' restored successfully.")
        except HistoryDatabaseError as e:
            await ctx.respond(f"❌ {e}")
        except Exception as e:
            logging.error(f"Error restoring checkpoint: {e}")
            await ctx.respond("❌ An error occurred while restoring the checkpoint.")

    #######################################################
    # Slash Command: checkpoint delete
    #######################################################
    @checkpoint.command(
        name="delete",
        description="Delete a checkpoint.",
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option("name", description="The name of the checkpoint to delete.", required=True, autocomplete=discord.utils.basic_autocomplete(_checkpoint_autocomplete))
    async def delete(self, ctx, name: str):
        await ctx.response.defer(ephemeral=True)

        view = discord.ui.View()
        confirm_button = discord.ui.Button(label="Confirm Delete", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")

        async def confirm_callback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
                return
            try:
                success = await self.DBConn.delete_checkpoint(guild_id=ctx.author.id, name=name)
                if success:
                    await interaction.response.edit_message(content=f"✅ Checkpoint '{name}' deleted successfully.", view=None)
                else:
                    await interaction.response.edit_message(content=f"❌ Checkpoint '{name}' not found.", view=None)
            except Exception as e:
                logging.error(f"Error deleting checkpoint: {e}")
                await interaction.response.edit_message(content="❌ An error occurred while deleting the checkpoint.", view=None)

        async def cancel_callback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("You are not authorized to perform this action.", ephemeral=True)
                return
            await interaction.response.edit_message(content="Cancelled checkpoint deletion.", view=None)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await ctx.respond(f"Are you sure you want to delete the checkpoint '{name}'?", view=view, ephemeral=True)
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
        autocomplete=discord.utils.basic_autocomplete(models.core.get_chat_models_autocomplete),
        required=True
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
        description="Clear the context history including the default model and agent settings",
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
        _agent = await self.DBConn.get_key(guild_id=ctx.author.id, key="tool_use")
        _model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_model")
        _openrouter_model = await self.DBConn.get_key(guild_id=ctx.author.id, key="default_openrouter_model")

        # Clear chat history
        await self.DBConn.clear_history(guild_id=ctx.author.id)

        if not reset_prefs:
            # Restore settings if not resetting preferences
            await self.DBConn.set_key(guild_id=ctx.author.id, key="tool_use", value=_agent)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_model", value=_model)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_openrouter_model", value=_openrouter_model)
            await ctx.respond("✅ Chat history reset!")
        else:
            await ctx.respond("✅ Chat history reset, model and agent settings are cleared!")



    #######################################################
    # Slash Command: agent
    #######################################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
    )
    @discord.option(
        "name",
        description="Integrate tools to chat! Setting chat agents will clear your history!",
        choices=models.core.get_tools_list_generator(),
    )
    async def agent(self, ctx, name: str):
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
        if name == "disabled":
            name = None

        if _current_agent == name:
            await ctx.respond("✅ Agent already set!")
        else:
            # Clear chat history IF the agent is not set to None
            if _current_agent:
                await self.DBConn.clear_history(guild_id=ctx.author.id)

            # Set new agent name and restore default model
            await self.DBConn.set_key(guild_id=ctx.author.id, key="tool_use", value=name)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_model", value=_model)
            await self.DBConn.set_key(guild_id=ctx.author.id, key="default_openrouter_model", value=_openrouter_model)

            if name is None:
                await ctx.respond("✅ Agents disabled and chat is reset to reflect the changes")
            else:
                # Return with actual tool name
                _actual_human_agent_name = await fetch_actual_tool_name(name)

                if not _current_agent:
                    await ctx.respond(f"✅ Agent **{_actual_human_agent_name}** enabled successfully")
                else:
                    await ctx.respond(f"✅ Agent **{_actual_human_agent_name}** enabled successfully and chat is reset to reflect the changes")

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
