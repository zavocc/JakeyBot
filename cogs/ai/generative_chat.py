from core.ai.core import ModelsList
from core.exceptions import *
from core.services.helperfunctions import HelperFunctions
from core.ai.history import History as typehint_History
from discord import Message
from models.utils import fetch_model
from models.providers.openai.completion import ChatSessionOpenAI
from os import environ
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

        # This is to ensure they don't perform inference concurrently
        self.pending_ids = []

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
        _model_alias = await fetch_model(model_alias=(await self.DBConn.get_default_model(guild_id=guild_id)))
        
        # Check what provider to call
        # TODO: add more checks, for now we lock in to OpenAI
        #if _model_alias.provider == "openai":
        _chat_session = ChatSessionOpenAI(
            user_id=guild_id,
            model_props=_model_alias,
            openai_client=self.bot._openai_client if hasattr(self.bot, "_openai_client") else None,
            discord_bot=self.bot,
            discord_context=prompt,
            db_conn=self.DBConn
        )

        # Check for /chat:ephemeral
        _append_history = True
        if "/chat:ephemeral" in prompt.content:
            await prompt.channel.send("🔒 This conversation is not saved and Jakey won't remember this")
            _append_history = False

        if "/chat:info" in prompt.content:
            _show_info = True
        else:
            _show_info = False

        ###############################################
        # File attachment processing
        ###############################################
        for _attachment in prompt.attachments:
            _processFileInterstitial = await prompt.channel.send(f"📄 Processing the file: **{_attachment.filename}**")
            await _chat_session.upload_files(attachment=_attachment)
            await _processFileInterstitial.edit(f"✅ Added: **{_attachment.filename}**")

        ###############################################
        # Answer generation
        ###############################################
        # Through capturing group, we can remove the mention and the model selection from the prompt at both in the middle and at the end
        _final_prompt = re.sub(rf"(<@{self.bot.user.id}>(\s|$)|\/chat:ephemeral(\s|$)|\/chat:info(\s|$))", "", prompt.content).strip()
        _system_prompt = await HelperFunctions.set_assistant_type("jakey_system_prompt", type=0)

        # Generate the response and simulate the typing
        async with prompt.channel.typing():
            # TODO: Call historydb function to query chat  history using get key and set key
            # WIP TODO: Call load history method and we can do checks here if it supports chat threads than completions part
            _result = await _chat_session.send_message(
                prompt=_final_prompt,
                system_instructions=_system_prompt
            )

        # WIP TODO: Check if _result is a list and has _show_info
        #if _result["response"] == "OK" and _show_info:
        #    await prompt.channel.send(
        #        embed=discord.Embed(
        #            description=f"Answered by **{_model_name}** by **{_model_provider}** {"(this response isn't saved)" if not _append_history else ''}",
        #        )
        #    )

        # Save to chat history
        # WIP TODO: Call save history method
        if _append_history:
            #if not hasattr(_infer, "save_to_history"):
            #    await prompt.channel.send("⚠️ This model doesn't allow saving the conversation")
            #else:
            #    await _infer.save_to_history(db_conn=self.DBConn, chat_thread=_result["chat_thread"])
            await prompt.channel.send("⚠️ Under Construction")

    async def on_message(self, message: Message):
        # Ignore messages from the bot itself
        if message.author.id == self.bot.user.id:
            return

        # Must be mentioned and check if it's not starts with prefix or slash command
        if message.guild is None or self.bot.user.mentioned_in(message):
            # Ensure it must not be triggered by command prefix or slash command
            if message.content.startswith(self.bot.command_prefix) or message.content.startswith("/"):
                # First we extract first word from the message see if this is a prefix command
                if message.content.startswith(self.bot.command_prefix):
                    _command = message.content.split(" ")[0].replace(self.bot.command_prefix, "")
                    if self.bot.get_command(_command):
                        return
                    
            # Check if the user is in the pending list
            if message.author.id in self.pending_ids:
                await message.reply("⚠️ I'm still processing your previous request, please wait for a moment...")
                return
            
            # Check if the bot was only mentioned without any content or image attachments
            # If none, then on main.py event, proceed sending the introductory message
            if not message.attachments \
                and not re.sub(f"<@{self.bot.user.id}>", '', message.content).strip():
                return
            
            # Remove the mention from the prompt
            message.content = re.sub(f"<@{self.bot.user.id}>", '', message.content).strip()

            # Check for image attachments, if exists, put the URL in the prompt
            # TODO: Support for multiple attachments
            #if message.attachments:
            #    _alttext = message.attachments[0].description if message.attachments[0].description else "No alt text provided"
            #    message.content = inspect.cleandoc(f"""<extra_metadata>
            #        <attachment url="{message.attachments[0].url}" />
            #        <alt>
            #            {_alttext}
            #        </alt>
            #    </extra_metadata>
            #
            #    {message.content}""")

            # If the bot is mentioned through reply with mentions, also add its previous message as context
            # So that the bot will reply to that query without quoting the message providing relevant response
            if message.reference:
                _context_message = await message.channel.fetch_message(message.reference.message_id)
                message.content = inspect.cleandoc(
                    f"""<reply_metadata>
                    
                    # Replying to referenced message excerpt from {_context_message.author.display_name} (username: @{_context_message.author.name}):
                    <|begin_msg_contexts|diff>
                    {_context_message.content}
                    <|end_msg_contexts|diff>
                    
                    <constraints>Do not echo this metadata, only use for retrieval purposes</constraints>
                    </reply_metadata>
                    {message.content}"""
                )
                await message.channel.send(f"✅ Referenced message: {_context_message.jump_url}")


            # For now the entire function is under try 
            # Maybe this can be separated into another function
            try:
                # Add the user to the pending list
                self.pending_ids.append(message.author.id)

                # Add reaction to the message to acknowledge the message
                await message.add_reaction("⌛")
                await self._ask(message)
            except Exception as _error:
                #if isinstance(_error, genai_errors.ClientError) or isinstance(_error, genai_errors.ServerError):
                #    await message.reply(f"😨 Uh oh, something happened to our end while processing request to Gemini API, reason: **{_error.message}**")
                if isinstance(_error, HistoryDatabaseError):
                    await message.reply(f"🤚 An error has occurred while running this command, there was problems accessing with database, reason: **{_error.message}**")
                elif isinstance(_error, ModelAPIKeyUnset):
                    await message.reply(f"⛔ The model you've chosen is not available at the moment, please choose another model, reason: **{_error.message}**")
                # Check if the error is about empty message
                elif isinstance(_error, discord.errors.HTTPException) and "Cannot send an empty message" in str(_error):
                    await message.reply("⚠️ I recieved an empty response, please rephrase your question or change another model")
                elif isinstance(_error, CustomErrorMessage):
                    await message.reply(f"{_error.message}")
                else:
                    # Check if the error has message attribute
                    #if hasattr(_error, "message"):
                    #    await message.reply(f"❌ Sorry, I couldn't answer your question at the moment, please try again later or change another model. What exactly happened: **{_error.message}**")
                    #else:
                    await message.reply(f"🚫 Sorry, I couldn't answer your question at the moment, please try again later or change another model. What exactly happened: **{type(_error).__name__}**")

                # Log the error
                logging.error("An error has occurred while generating an answer, reason: ", exc_info=True)
            finally:
                # Remove the reaction
                await message.remove_reaction("⌛", self.bot.user)

                # Remove the user from the pending list
                self.pending_ids.remove(message.author.id)

    
