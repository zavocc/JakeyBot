from core.ai.core import ModelsList
from core.exceptions import ModelUnavailable, MultiModalUnavailable, ToolsUnavailable
from core.ai.history import History # type hinting
from discord.ext import commands
from discord import Message
from os import environ
import core.ai.models._template_.infer # For type hinting
import aiofiles
import aiofiles.os
import discord
import importlib
import logging
import random
import re

class BaseChat():
    def __init__(self, bot, author, history: History, assistants):
        self.bot: discord.Bot = bot
        self.author = author
        self.DBConn = history
        self._assistants_system_prompt = assistants

    ###############################################
    # Events-based chat
    ###############################################
    # This is a private function
    async def priv_ask(self, prompt: Message):
        # Check if SHARED_CHAT_HISTORY is enabled
        if environ.get("SHARED_CHAT_HISTORY", "false").lower() == "true":
            guild_id = prompt.guild.id if prompt.guild else prompt.author.id # Always fallback to ctx.author.id for DMs since ctx.guild is None
        else:
            guild_id = prompt.author.id

        # Thinking message
        _thinking_message = await prompt.channel.send("🤔 Determining what to do...")

        # Check if we can switch models
        try:
            _model = await self.DBConn.get_default_model(guild_id=guild_id)
        except Exception as e:
            # Set the default model
            _model = "__gemini__gemini-1.5-flash-002"
            logging.error("generative_event.py: Something went wrong while getting default model %s", e)

        _model_provider = _model.split("::")[0]
        _model_name = _model.split("::")[-1]
        if "/model:" in prompt.content:
            await _thinking_message.edit(f"🔍 Using specific model")
            async for _model_selection in ModelsList.get_models_list_async():
                _model_provider = _model_selection.split("::")[0]
                _model_name = _model_selection.split("::")[-1]

                # In this regex, we are using \s at the end since when using gpt-4o-mini, it will match with gpt-4o at first
                # So, we are using \s|$ to match the end of the string and the suffix gets matched or if it's placed at the end of the string
                if re.search(rf"\/model:{_model_name}(\s|$)", prompt.content):
                    await _thinking_message.edit(content=f"🔍 Asking with specific model: **{_model_name}**")
                    break
            else:
                _model_provider = _model.split("::")[0]
                _model_name = _model.split("::")[-1]
                await _thinking_message.edit(content=f"🔍 Asking with the default model: **{_model_name}**")
    
        # Check for /chat:ephemeral and /chat:info
        _append_history = True
        _show_info = False
        if "/chat:ephemeral" in prompt.content:
            await _thinking_message.edit("🔒 Ok the user wants me to not save this conversation so I will respect that")
            _append_history = False
        if "/chat:info" in prompt.content:
            await _thinking_message.edit("ℹ️ Ok the user wants me to show the information about the model, tool, files used")
            _show_info = True

        try:
            _infer: core.ai.models._template_.infer.Completions = importlib.import_module(f"core.ai.models.{_model_provider}.infer").Completions(
                    guild_id=guild_id,
                    model_name=_model_name,
                    db_conn = self.DBConn,
            )
        except ModuleNotFoundError:
            raise ModelUnavailable
        _infer._discord_method_send = prompt.channel.send

        ###############################################
        # File attachment processing
        ###############################################
        if len(prompt.attachments) > 1:
            await _thinking_message.edit("🚫 I can only process one file at a time")
            return
        
        if prompt.attachments:
            if not hasattr(_infer, "input_files"):
                raise MultiModalUnavailable

            await _thinking_message.edit(f"📄 Processing the file: **{prompt.attachments[0].filename}**")
            await _infer.input_files(attachment=prompt.attachments[0])

        ###############################################
        # Answer generation
        ###############################################
        await _thinking_message.edit(f"⌛ Formulating an answer...")

        # Through capturing group, we can remove the mention and the model selection from the prompt at both in the middle and at the end
        _final_prompt = re.sub(rf"(<@{self.bot.user.id}>(\s|$)|\/model:{_model_name}(\s|$)|\/chat:ephemeral(\s|$)|\/chat:info(\s|$))", "", prompt.content).strip()
        # If we have attachments, also add the URL to the prompt so that it can be used for tools
        if prompt.attachments:
            _final_prompt += f"\n\nTHIS PROMPT IS AUTO INSERTED BY SYSTEM: By the way based on the attachment given, here is the URL associated for reference:\n{prompt.attachments[0].url}"
        
        _result = await _infer.chat_completion(prompt=_final_prompt, system_instruction=self._assistants_system_prompt.jakey_system_prompt)
        
        # Format the response
        _formatted_response = _result["answer"].rstrip()

        # Delete the thinking message
        await _thinking_message.delete()

        # Model usage and context size
        if len(_result["answer"]) > 2000 and len(_result["answer"]) < 4096:
            _system_embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(_final_prompt)[0:100],
                description=str(_result["answer"]),
                color=discord.Color.random()
            )
        else:
            if _show_info:
                _system_embed = discord.Embed()
            else:
                _system_embed = None
                # Add minified version of chat information
                _formatted_response = f"{_result['answer'].rstrip()}\n-# {_model_name.upper()} {"(this response isn't saved)" if not _append_history else ''}"

        if not _system_embed is None:
            # Model used
            _system_embed.add_field(name="Model used", value=_model_name)
                
            # Check if this conversation isn't appended to chat history
            if not _append_history: _system_embed.add_field(name="Privacy", value="This conversation isn't saved")

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
        if _append_history:
            await _infer.save_to_history(chat_thread=_result["chat_thread"])

    async def on_message(self, prompt_message: Message):
        # Ignore messages from the bot itself
        if prompt_message.author.id == self.bot.user.id:
            return

        # Must be mentioned and check if it's not starts with prefix or slash command
        if prompt_message.guild is None or self.bot.user.mentioned_in(prompt_message):
            if prompt_message.content.startswith(self.bot.command_prefix) or prompt_message.content.startswith("/"):
                return
            
            # Check if the prompt is empty
            if prompt_message.content == f"<@{self.bot.user.id}>".strip():
                return

            # For now the entire function is under try 
            # Maybe this can be separated into another function
            try:
                await self.priv_ask(prompt_message)
            except Exception as _error:
                if isinstance(_error, commands.CommandOnCooldown):
                    await prompt_message.reply(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
                elif isinstance(_error, MultiModalUnavailable):
                    await prompt_message.reply("🚫 This model cannot process certain files, choose another model to continue")
                elif isinstance(_error, ModelUnavailable):
                    await prompt_message.reply(f"⚠️ The model you've chosen is not available at the moment, please choose another model")
                elif isinstance(_error, ToolsUnavailable):
                    await prompt_message.reply(f"⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")
                else:
                    await prompt_message.reply(f"❌ Sorry, I couldn't answer your question at the moment, reason:\n```{_error}```")

                # Raise error
                raise _error
    
