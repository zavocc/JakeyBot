from core.ai.assistants import Assistants
from core.ai.core import ModelsList
from core.exceptions import *
from core.ai.history import History # type hinting
from discord import Message
from google.genai import errors as genai_errors
from os import environ
import core.aimodels._template_ # For type hinting
import discord
import importlib
import inspect
import io
import logging
import re

class BaseChat():
    def __init__(self, bot, author, history: History):
        self.bot: discord.Bot = bot
        self.author = author
        self.DBConn = history

    ###############################################
    # Events-based chat
    ###############################################
    async def _ask(self, prompt: Message):
        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = prompt.guild.id if prompt.guild else prompt.author.id # Always fallback to ctx.author.id for DMs since ctx.guild is None
        else:
            guild_id = prompt.author.id

        # Set default model
        _model = await self.DBConn.get_default_model(guild_id=guild_id)
        if _model is None:
            logging.info("No default model found, using default model")
            _model = "gemini::gemini-1.5-flash-002"

        _model_provider = _model.split("::")[0]
        _model_name = _model.split("::")[-1]
        if "/model:" in prompt.content:
            _modelUsed = await prompt.channel.send(f"🔍 Using specific model")
            async for _model_selection in ModelsList.get_models_list_async():
                _model_provider = _model_selection.split("::")[0]
                _model_name = _model_selection.split("::")[-1]

                # In this regex, we are using \s at the end since when using gpt-4o-mini, it will match with gpt-4o at first
                # So, we are using \s|$ to match the end of the string and the suffix gets matched or if it's placed at the end of the string
                if re.search(rf"\/model:{_model_name}(\s|$)", prompt.content):
                    await _modelUsed.edit(content=f"🔍 Using model: **{_model_name}**")
                    break
            else:
                _model_provider = _model.split("::")[0]
                _model_name = _model.split("::")[-1]
                await _modelUsed.edit(content=f"🔍 Using model: **{_model_name}**")
    
        # Check for /chat:ephemeral
        _append_history = True
        if "/chat:ephemeral" in prompt.content:
            await prompt.channel.send("🔒 This conversation is not saved and Jakey won't remember this")
            _append_history = False
      
        try:
            _infer: core.aimodels._template_.Completions = importlib.import_module(f"core.aimodels.{_model_provider}").Completions(
                discord_ctx=prompt,
                discord_bot=self.bot,
                guild_id=guild_id,
                model_name=_model_name)
        except ModuleNotFoundError:
            raise CustomErrorMessage("⚠️ The model you've chosen is not available at the moment, please choose another model")
        _infer._discord_method_send = prompt.channel.send

        ###############################################
        # File attachment processing
        ###############################################
        if len(prompt.attachments) > 1:
            await prompt.reply("🚫 I can only process one file at a time")
            return
        
        if prompt.attachments:
            if not hasattr(_infer, "input_files"):
                raise CustomErrorMessage("🚫 This model cannot process file attachments, please try another model")

            _processFileInterstitial = await prompt.channel.send(f"📄 Processing the file: **{prompt.attachments[0].filename}**")
            await _infer.input_files(attachment=prompt.attachments[0])
            await _processFileInterstitial.edit(f"✅ Used: **{prompt.attachments[0].filename}**")

        ###############################################
        # Answer generation
        ###############################################
        # Through capturing group, we can remove the mention and the model selection from the prompt at both in the middle and at the end
        _final_prompt = re.sub(rf"(<@{self.bot.user.id}>(\s|$)|\/model:{_model_name}(\s|$)|\/chat:ephemeral(\s|$))", "", prompt.content).strip()
        # If we have attachments, also add the URL to the prompt so that it can be used for tools
        if prompt.attachments:
            _final_prompt += f"\n\nThis additional prompt metadata is autoinserted by system:\nAttachment URL of the data provided for later reference: {prompt.attachments[0].url}"
        
        _system_prompt = await Assistants.set_assistant_type("jakey_system_prompt", type=0)

        # Generate the response and simulate the typing
        async with prompt.channel.typing():
            _result = await _infer.chat_completion(prompt=_final_prompt, db_conn=self.DBConn, system_instruction=_system_prompt)
        
        # Format the response
        _formatted_response = _result["answer"].rstrip()

        # Model usage and context size
        if len(_formatted_response) > 2000 and len(_formatted_response) < 4096:
            _system_embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=_final_prompt.replace("\n", " ")[0:20] + "...",
                description=str(_formatted_response),
                color=discord.Color.random()
            )
        else:
            _system_embed = None
        
        # Model information footer
        _modelInfoFooter = f"-# Chatting with {_model_name.upper()} {"(this response isn't saved)" if not _append_history else ''}"

        if _system_embed: 
            # Check if there is _tokens_used attribute
            if hasattr(_infer, "_tokens_used"):
                _system_embed.add_field(name="Tokens used", value=_infer._tokens_used)

            # Files used
            if prompt.attachments: 
                _system_embed.add_field(name="File used", value=prompt.attachments[0].filename)
            _system_embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_formatted_response) > 4096:
            # Send the response as file
            await prompt.channel.send("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(io.StringIO(_formatted_response), "response.md"), embed=_system_embed)
        elif len(_formatted_response) > 2000:
            await prompt.channel.send(embed=_system_embed)
        else:
            await prompt.channel.send(_formatted_response, embed=_system_embed)

        # Show model information
        await prompt.channel.send(_modelInfoFooter)

        # Save to chat history
        if _append_history:
            await _infer.save_to_history(db_conn=self.DBConn, chat_thread=_result["chat_thread"])

    async def on_message(self, pmessage: Message):
        # Ignore messages from the bot itself
        if pmessage.author.id == self.bot.user.id:
            return

        # Must be mentioned and check if it's not starts with prefix or slash command
        if pmessage.guild is None or self.bot.user.mentioned_in(pmessage):
            # Ensure it must not be triggered by command prefix or slash command
            if pmessage.content.startswith(self.bot.command_prefix) or pmessage.content.startswith("/"):
                return
            
            # Check if the bot was only mentioned without any content or image attachments
            # If none, then on main.py event, proceed sending the introductory message
            if not pmessage.attachments \
                and not re.sub(f"<@{self.bot.user.id}>", '', pmessage.content).strip():
                return
            
            # If the bot is mentioned through reply with mentions, also add its previous message as context
            # So that the bot will reply to that query without quoting the message providing relevant response
            if pmessage.reference:
                _context_message = await pmessage.channel.fetch_message(pmessage.reference.message_id)
                pmessage.content = inspect.cleandoc(
                    f"""# Replying to referenced message excerpt from {_context_message.author.display_name} (username: @{_context_message.author.name}):
                    <|begin_msg_contexts|>
                    {_context_message.content}
                    <|end_msg_contexts|>

                    ## Actual question, answer this prompt with the referenced message context mentioned above:
                    <|begin_usr_question|>
                    {pmessage.content}
                    <|end_usr_question|>"""
                )
                await pmessage.channel.send(f"✅ Referenced message: {_context_message.jump_url}")

            # For now the entire function is under try 
            # Maybe this can be separated into another function
            try:
                # Add reaction to the message to acknowledge the message
                await pmessage.add_reaction("🤖")
                await self._ask(pmessage)
            except Exception as _error:
                if isinstance(_error, genai_errors.ClientError) or isinstance(_error, genai_errors.ServerError):
                    await pmessage.reply(f"😨 Uh oh, something happened to our end while processing request to Gemini API, reason: \n> {_error.message}")
                elif isinstance(_error, HistoryDatabaseError):
                    await pmessage.reply(f"🤚 An error has occurred while running this command, there was problems accessing with database, reason: **{_error.message}**")
                elif isinstance(_error, CustomErrorMessage):
                    await pmessage.reply(f"{_error.message}")
                # Check if the error is about empty message
                elif isinstance(_error, discord.errors.HTTPException) and "Cannot send an empty message" in str(_error):
                    await pmessage.reply("⚠️ I recieved an empty response, please rephrase your question or change another model")
                else:
                    # Handles all errors including from LiteLLM
                    # https://docs.litellm.ai/docs/exception_mapping#litellm-exceptions
                    await pmessage.reply(f"❌ Sorry, I couldn't answer your question at the moment, check console logs or change another model. What exactly happened: **`{type(_error).__name__}`**")

                # Log the error
                logging.error("An error has occurred while generating an answer, reason: ", exc_info=True)
            finally:
                # Remove the reaction
                await pmessage.remove_reaction("🤖", self.bot.user)

    
