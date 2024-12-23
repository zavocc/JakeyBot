from core.ai.assistants import Assistants
from core.exceptions import ModelUnavailable, MultiModalUnavailable
from os import environ
import core.aimodels._template_ # For type hinting
import discord
import importlib
import io
import logging

class BaseChat():
    def __init__(self, bot, author, history):
        self.bot: discord.Bot = bot
        self.author = author
        self.DBConn = history

    ###############################################
    # Ask slash command
    ###############################################
    async def ask(self, ctx: discord.ApplicationContext, prompt: str, attachment: discord.Attachment, model: str,
        append_history: bool, show_info: bool):
        await ctx.response.defer(ephemeral=False)

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
        if model is None:
            # Set default model
            _model = await self.DBConn.get_default_model(guild_id=guild_id)
            if _model is None:
                logging.info("No default model found, using default optimized model")
                _model = "gemini::gemini-1.5-flash-002"
        else:
            _model = model

        _model = _model.split("::")
        _model_provider = _model[0]
        _model_name = _model[-1]

        # Configure inference
        try:
            _infer: core.aimodels._template_.Completions = importlib.import_module(f"core.aimodels.{_model_provider}").Completions(
                discord_ctx=ctx,
                discord_bot=self.bot,
                guild_id=guild_id,
                model_name=_model_name)
        except ModuleNotFoundError:
            raise ModelUnavailable(f"⚠️ The model you've chosen is not available at the moment, please choose another model")

        ###############################################
        # File attachment processing
        ###############################################
        if attachment is not None:
            if not hasattr(_infer, "input_files"):
                raise MultiModalUnavailable("🚫 This model cannot process file attachments, please try another model")

            await _infer.input_files(attachment=attachment)

            # Also add the URL to the prompt so that it can be used for tools
            prompt += f"\n\nThis additional prompt metadata is autoinserted by system:\nAttachment URL of the data provided for later reference: {attachment.url}"

        ###############################################
        # Answer generation
        ###############################################
        _system_prompt = await Assistants.set_assistant_type("jakey_system_prompt", type=0)
        _result = await _infer.chat_completion(prompt=prompt, db_conn=self.DBConn, system_instruction=_system_prompt)
        _formatted_response = _result["answer"].rstrip()

        # Model usage and context size
        if len(_formatted_response) > 2000 and len(_formatted_response) < 4096:
            _system_embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(prompt)[0:15] + "...",
                description=str(_formatted_response),
                color=discord.Color.random()
            )
        else:
            if show_info:
                _system_embed = discord.Embed(description="Chat information")
                _minifiedModelInfoInterstitial = None
            else:
                _system_embed = None
                _minifiedModelInfoInterstitial = f"-# {_model_name.upper()} {"(this response isn't saved)" if not append_history else ''}"

        if _system_embed:
            # Model used
            _system_embed.add_field(name="Model used", value=_model_name)

            # Check if this conversation isn't appended to chat history
            if not append_history: 
                _system_embed.add_field(name="Privacy", value="This conversation isn't saved")

            # Check if there is _tokens_used attribute
            if hasattr(_infer, "_tokens_used"):
                _system_embed.add_field(name="Tokens used", value=_infer._tokens_used)
                
            # Files used
            if attachment is not None: 
                _system_embed.add_field(name="File used", value=attachment.filename)
            _system_embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_formatted_response) > 4096:
            # Send the response as file
            _jakey_response = await ctx.send("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(io.StringIO(_formatted_response), "response.md"), embed=_system_embed)
        elif len(_formatted_response) > 2000:
            # Since this is already an embed, we don't need minified interstitial
            _minifiedModelInfoInterstitial = None
            _jakey_response = await ctx.send(embed=_system_embed)
        else:
            _jakey_response = await ctx.send(_formatted_response, embed=_system_embed)
        
        if _minifiedModelInfoInterstitial:
            await ctx.send(_minifiedModelInfoInterstitial)

        # Save to chat history
        if append_history:
            await _infer.save_to_history(db_conn=self.DBConn, chat_thread=_result["chat_thread"])

        # Done
        await ctx.respond(f"✅ Done {ctx.author.mention}! check out the response: {_jakey_response.jump_url}")