from core.ai.assistants import Assistants
from core.ai.core import ModelsList
from core.exceptions import *
from core.ai.history import History as typehint_History
from discord import Message
from os import environ
import core.aimodels._template_ as typehint_AIModelTemplate
import discord
import importlib
import inspect
import logging
import re

class BaseChat():
    def __init__(self, bot, author, history: typehint_History):
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
            _model = "gemini::gemini-2.0-flash-001"

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
            _infer: typehint_AIModelTemplate.Completions = importlib.import_module(f"core.aimodels.{_model_provider}").Completions(
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
                raise CustomErrorMessage(f"🚫 The model **{_model_name}** cannot process file attachments, please try another model")

            _processFileInterstitial = await prompt.channel.send(f"📄 Processing the file: **{prompt.attachments[0].filename}**")
            await _infer.input_files(
                attachment=prompt.attachments[0], 
                extra_metadata=f"This additional an metadata is autoinserted by system:\nAttachment URL of the data provided for later reference: {prompt.attachments[0].url}"
            )
            await _processFileInterstitial.edit(f"✅ Used: **{prompt.attachments[0].filename}**")

        ###############################################
        # Answer generation
        ###############################################
        # Through capturing group, we can remove the mention and the model selection from the prompt at both in the middle and at the end
        _final_prompt = re.sub(rf"(<@{self.bot.user.id}>(\s|$)|\/model:{_model_name}(\s|$)|\/chat:ephemeral(\s|$))", "", prompt.content).strip()
        _system_prompt = await Assistants.set_assistant_type("jakey_system_prompt", type=0)

        # Generate the response and simulate the typing
        async with prompt.channel.typing():
            _result = await _infer.chat_completion(prompt=_final_prompt, db_conn=self.DBConn, system_instruction=_system_prompt)

        # Check if result says "OK"
        if _result["response"] == "OK":
            await prompt.channel.send(
                embed=discord.Embed(
                    description=f"Answered by **{_model_name}** by **{_model_provider}** {"(this response isn't saved)" if not _append_history else ''}",
                )
            )

        # Save to chat history
        if _append_history:
            await _infer.save_to_history(db_conn=self.DBConn, chat_thread=_result["chat_thread"])
        else:
            await prompt.channel.send("⚠️ This model doesn't allow saving the conversation")

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
                await pmessage.add_reaction("⌛")
                await self._ask(pmessage)
            except Exception as _error:
                #if isinstance(_error, genai_errors.ClientError) or isinstance(_error, genai_errors.ServerError):
                #    await pmessage.reply(f"😨 Uh oh, something happened to our end while processing request to Gemini API, reason: **{_error.message}**")
                if isinstance(_error, HistoryDatabaseError):
                    await pmessage.reply(f"🤚 An error has occurred while running this command, there was problems accessing with database, reason: **{_error.message}**")
                elif isinstance(_error, ModelAPIKeyUnset):
                    await pmessage.reply(f"⛔ The model you've chosen is not available at the moment, please choose another model, reason: **{_error.message}**")
                # Check if the error is about empty message
                elif isinstance(_error, discord.errors.HTTPException) and "Cannot send an empty message" in str(_error):
                    await pmessage.reply("⚠️ I recieved an empty response, please rephrase your question or change another model")
                elif isinstance(_error, CustomErrorMessage):
                    await pmessage.reply(f"{_error.message}")
                else:
                    # Check if the error has message attribute
                    #if hasattr(_error, "message"):
                    #    await pmessage.reply(f"❌ Sorry, I couldn't answer your question at the moment, please try again later or change another model. What exactly happened: **{_error.message}**")
                    #else:
                    await pmessage.reply(f"🚫 Sorry, I couldn't answer your question at the moment, please try again later or change another model. What exactly happened: **{type(_error).__name__}**")

                # Log the error
                logging.error("An error has occurred while generating an answer, reason: ", exc_info=True)
            finally:
                # Remove the reaction
                await pmessage.remove_reaction("⌛", self.bot.user)

    
