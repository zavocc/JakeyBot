from core.ai.assistants import Assistants
from core.ai.core import ModelsList
from core.ai.history import History
from core.exceptions import ChatHistoryFull, MultiModalUnavailable
from discord.ext import commands
from discord import Message
from os import environ
import core.ai.models._template_.infer # For type hinting
import aiofiles
import aiofiles.os
import discord
import importlib
import motor.motor_asyncio
import random
import re

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

        # default system prompt - load assistants
        self._assistants_system_prompt = Assistants()

    ###############################################
    # Ask command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @commands.cooldown(3, 6, commands.BucketType.user) # Add cooldown to prevent abuse
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
        "show_info",
        description="Show information about the model, tool, files used and the context size through an embed",
        default=False
    )
    async def ask(self, ctx, prompt: str, attachment: discord.Attachment, model: str,
        append_history: bool, show_info: bool):
        """Ask a question using Gemini and models from OpenAI, Anthropic, and more!"""
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

        # Set model
        _model = model.split("__")
        _model_provider = _model[1]
        _model_name = _model[-1]

        # Configure inference
        _infer: core.ai.models._template_.infer.Completions = importlib.import_module(f"core.ai.models.{_model_provider}.infer").Completions(
            guild_id=guild_id,
            model_name=_model_name,
            db_conn = self.DBConn,
        )
        _infer._discord_method_send = ctx.send

        ###############################################
        # File attachment processing
        ###############################################
        if attachment is not None:
            if not hasattr(_infer, "input_files"):
                raise MultiModalUnavailable(f"Multimodal is not available for this model: {_model_name}")

            await _infer.input_files(attachment=attachment)

        ###############################################
        # Answer generation
        ###############################################
        _result = await _infer.chat_completion(prompt=prompt, system_instruction=self._assistants_system_prompt.jakey_system_prompt)
        _formatted_response = _result["answer"].rstrip()

        # Model usage and context size
        if len(_result["answer"]) > 2000 and len(_result["answer"]) < 4096:
            _system_embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(prompt)[0:100],
                description=str(_result["answer"]),
                color=discord.Color.random()
            )
        else:
            if show_info:
                _system_embed = discord.Embed()
            else:
                _system_embed = None
                _formatted_response = f"{_result['answer'].rstrip()}\n-# {_model_name.upper()}"

        if not _system_embed is None:
            # Model used
            _system_embed.add_field(name="Model used", value=_model_name)
            # Only report context size information if history is enabled
            if append_history: 
                _system_embed.add_field(name="Chat turns left", value=f"{_result["prompt_count"]} of {environ.get('MAX_CONTEXT_HISTORY', 20)}")
            else:
                _system_embed.add_field(name="Chat turns left", value="This chat isn't saved")
                
            # Tool use
            if hasattr(_infer, "_used_tool_name"): _system_embed.add_field(name="Tool used", value=_infer._used_tool_name)
            # Files used
            if attachment is not None: _system_embed.add_field(name="File used", value=attachment.filename)
            _system_embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_formatted_response) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            async with aiofiles.open(response_file, "w+") as f:
                await f.write(_formatted_response)
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"), embed=_system_embed)
        elif len(_formatted_response) > 2000:
            await ctx.respond(embed=_system_embed)
        else:
            await ctx.respond(_formatted_response, embed=_system_embed)

        # Save to chat history
        if append_history:
            await _infer.save_to_history(chat_thread=_result["chat_thread"], prompt_count=_result["prompt_count"])

    @ask.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        _error = getattr(error, "original", error)
        # Cooldown error
        if isinstance(_error, commands.CommandOnCooldown):
            await ctx.respond(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
        elif isinstance(_error, ChatHistoryFull):
            await ctx.respond("📚 Maximum context history reached! Clear the conversation using `/sweep` to continue")
        elif isinstance(_error, MultiModalUnavailable):
            await ctx.respond("🚫 This model cannot process certain files, choose another model to continue")
        else:
            await ctx.respond(f"❌ Sorry, I couldn't answer your question at the moment, reason:\n```{_error}```")

        # Raise error
        raise _error

    @commands.Cog.listener()
    async def on_message(self, prompt: Message):
        # Must be mentioned
        if not self.bot.user.mentioned_in(prompt):
            return

        # Check if the prompt is empty
        if prompt.content == f"<@{self.bot.user.id}>":
            return

        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = prompt.guild.id if prompt.guild else prompt.author.id # Always fallback to ctx.author.id for DMs since ctx.guild is None
        else:
            guild_id = prompt.author.id

        # Check if we can switch models
        _model_provider = "gemini"
        _model_name = "gemini-1.5-flash-002"
        if "/model:" in prompt.content:
            _amsg = await prompt.channel.send(f"🔍 Using specific model")
            for _model_selection in ModelsList.get_models_list(raw=True):
                _model_provider = _model_selection.split("__")[1]
                _model_name = _model_selection.split("__")[-1]

                # In this regex, we are using \s at the end since when using gpt-4o-mini, it will match with gpt-4o at first
                # So, we are using \s|$ to match the end of the string and the suffix gets matched or if it's placed at the end of the string
                if re.search(rf"\/model:{_model_name}(\s|$)", prompt.content):
                    await _amsg.edit(content=f"🔍 Used specific model: {_model_name}")
                    break
    
        _infer: core.ai.models._template_.infer.Completions = importlib.import_module(f"core.ai.models.{_model_provider}.infer").Completions(
                guild_id=guild_id,
                model_name=_model_name,
                db_conn = self.DBConn,
        )
        _infer._discord_method_send = prompt.channel.send

        ###############################################
        # File attachment processing
        ###############################################
        if len(prompt.attachments) > 1:
            await prompt.channel.send("🚫 I can only process one file at a time")
            return
        
        if prompt.attachments:
            if not hasattr(_infer, "input_files"):
                raise MultiModalUnavailable(f"Multimodal is not available for this model: {_model_name}")

            await _infer.input_files(attachment=prompt.attachments[0])

        ###############################################
        # Answer generation
        ###############################################
        # Remove the mention substring
        #_removed_mentions = prompt.content.replace(f"<@{self.bot.user.id}>", "").strip()

        # Through capturing group, we can remove the mention and the model selection from the prompt at both in the middle and at the end
        _final_prompt = re.sub(rf"(<@{self.bot.user.id}>(\s|$)|\/model:{_model_name}(\s|$))", "", prompt.content).strip()
        print(_final_prompt)
        _result = await _infer.chat_completion(prompt=_final_prompt, system_instruction=self._assistants_system_prompt.jakey_system_prompt)
        
        # Format the response
        _formatted_response = _result["answer"].rstrip()

        # Model usage and context size
        if len(_result["answer"]) > 2000 and len(_result["answer"]) < 4096:
            _system_embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(_final_prompt)[0:100],
                description=str(_result["answer"]),
                color=discord.Color.random()
            )
        else:
            _system_embed = None
            _formatted_response = f"{_result['answer'].rstrip()}\n-# {_model_name.upper()}"

        if not _system_embed is None:
            # Model used
            _system_embed.add_field(name="Model used", value=_model_name)
            # Only report context size information if history is enabled
            _system_embed.add_field(name="Chat turns left", value=f"{_result["prompt_count"]} of {environ.get('MAX_CONTEXT_HISTORY', 20)}")
                
            # Tool use
            if hasattr(_infer, "_used_tool_name"): _system_embed.add_field(name="Tool used", value=_infer._used_tool_name)
            # Files used
            if prompt.attachments: _system_embed.add_field(name="File used", value=prompt.attachments[0].filename)
            _system_embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_formatted_response) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            async with aiofiles.open(response_file, "w+") as f:
                await f.write(_formatted_response)
            await prompt.channel.send("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"), embed=_system_embed)
        elif len(_formatted_response) > 2000:
            await prompt.channel.send(embed=_system_embed)
        else:
            await prompt.channel.send(_formatted_response, embed=_system_embed)

        # Save to chat history
        await _infer.save_to_history(chat_thread=_result["chat_thread"], prompt_count=_result["prompt_count"])

    