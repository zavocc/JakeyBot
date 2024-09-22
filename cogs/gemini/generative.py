from core.ai.assistants import Assistants
from core.ai.core import GenAIConfigDefaults, ModelsList
from core.ai.history import History
from discord.ext import commands
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from os import environ, remove
from pathlib import Path
import google.generativeai as genai
import google.api_core.exceptions
import aiohttp
import aiofiles
import asyncio
import discord
import importlib
import inspect
import jsonpickle
import logging
import motor.motor_asyncio
import random

class BaseChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Logging format
        # LEVEL NAME: (message)
        logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

        # Load the database and initialize the HistoryManagement class
        # MongoDB database connection for chat history and possibly for other things
        try:
            self.HistoryManagement: History = History(db_conn=motor.motor_asyncio.AsyncIOMotorClient(environ.get("MONGO_DB_URL")))
        except Exception as e:
            raise e(f"Failed to connect to MongoDB: {e}...\n\nPlease set MONGO_DB_URL in dev.env")

        # Check for gemini API keys
        if environ.get("GOOGLE_AI_TOKEN") is None or environ.get("GOOGLE_AI_TOKEN") == "INSERT_API_KEY":
            raise Exception("GOOGLE_AI_TOKEN is not configured in the dev.env file. Please configure it and try again.")
        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

        # Initialize GenAIConfigDefaults
        self._genai_configs = GenAIConfigDefaults()

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
        default="gemini-1.5-flash-001",
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

        # Load and deserialize the chat data
        _prompt_count, _chat_thread = await self.HistoryManagement.load_history(guild_id=guild_id)
        _chat_thread = jsonpickle.decode(_chat_thread, keys=True) if _chat_thread is not None else []

        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise MemoryError("Maximum history reached! Clear the conversation")

        # Import tool
        _Tool = importlib.import_module(f"tools.{(await self.HistoryManagement.get_config(guild_id=guild_id))}").Tool(self.bot, ctx)

        # check if its a code_execution
        if _Tool.tool_name == "code_execution":
            _Tool.tool_schema = "code_execution"
        
        # Model configuration - the default model is flash
        model_to_use = genai.GenerativeModel(model_name=model, safety_settings=self._genai_configs.safety_settings_config, generation_config=self._genai_configs.generation_config, system_instruction=self._assistants_system_prompt.jakey_system_prompt, tools=_Tool.tool_schema)

        ###############################################
        # File attachment processing
        ###############################################
        _xfile_uri = None
        # Enable multimodal support if an attachment is provided
        if attachment:
            # Pass attachment URL to the tool
            if hasattr(_Tool, "file_uri"):
                _Tool.file_uri = attachment.url

            # Download the attachment
            _xfilename = f"{environ.get('TEMP_DIR')}/JAKEY.{guild_id}.{random.randint(5000, 6000)}.{attachment.filename}"
            try:
                async with aiohttp.ClientSession(raise_for_status=True) as session:
                    async with session.get(attachment.url, allow_redirects=True) as _xattachments:
                        # write to file with random number ID
                        async with aiofiles.open(_xfilename, "wb") as filepath:
                            async for _chunk in _xattachments.content.iter_chunked(8192):
                                await filepath.write(_chunk)
            except aiohttp.ClientError as httperror:
                # Remove the file if it exists ensuring no data persists even on failure
                if Path(_xfilename).exists():
                    remove(_xfilename)
                # Raise exception
                raise httperror

            # Upload the file to the server
            try:
                _xfile_uri = await asyncio.to_thread(genai.upload_file, path=_xfilename, display_name=_xfilename.split("/")[-1])
                _x_msgstatus = None

                # Wait for the file to be uploaded
                while _xfile_uri.state.name == "PROCESSING":
                    if _x_msgstatus is None:
                        _x_msgstatus = await ctx.send("⌛ Processing the file attachment... this may take a while")
                    await asyncio.sleep(3)
                    _xfile_uri = await asyncio.to_thread(genai.get_file, _xfile_uri.name)

                if _xfile_uri.state.name == "FAILED":
                    await ctx.respond("❌ Sorry, I can't process the file attachment. Please try again.")
                    raise ValueError(_xfile_uri.state.name)
            except Exception as e:
                await ctx.respond(f"❌ An error has occured when uploading the file or the file format is not supported\nLog:\n```{e}```")
                remove(_xfilename)
                return

            # Immediately use the "used" status message to indicate that the file API is used
            if verbose_logs:
                if _x_msgstatus is not None:
                    await _x_msgstatus.edit(content=f"Used: **{attachment.filename}**")
                else:
                    await ctx.send(f"Used: **{attachment.filename}**")

                # Add caution that the attachment data would be lost in 48 hours
                await ctx.send("> 📝 **Note:** The submitted file attachment will be deleted from the context after 48 hours.")
                await _x_msgstatus.delete()

            # Remove the file from the temp directory
            remove(_xfilename)

        if not attachment and hasattr(_Tool, "file_uri"):
            _Tool.tool_config = "NONE"

        ###############################################
        # Answer generation
        ###############################################
        final_prompt = [_xfile_uri, f'{prompt}'] if _xfile_uri is not None else f'{prompt}'
        chat_session = model_to_use.start_chat(history=_chat_thread)

        # Re-write the history if an error has occured
        # For now this is the only workaround that I could find to re-write the history if there are dead file references causing PermissionDenied exception
        # when trying to access the deleted file uploaded using Files API. See:
        # https://discuss.ai.google.dev/t/what-is-the-best-way-to-persist-chat-history-into-file/3804/6?u=zavocc306
        try:
            answer = await chat_session.send_message_async(final_prompt, tool_config={'function_calling_config':_Tool.tool_config})
        #  Retry the response if an error has occured
        except google.api_core.exceptions.PermissionDenied:
            _chat_thread = [
                {"role": x.role, "parts": [y.text]} 
                for x in chat_session.history 
                for y in x.parts 
                if x.role and y.text
            ]

            # Notify the user that the chat session has been re-initialized
            await ctx.send("> ⚠️ One or more file attachments or tools have been expired, the chat history has been reinitialized!")

            # Re-initialize the chat session
            chat_session = model_to_use.start_chat(history=_chat_thread, tool_config={'function_calling_config':_Tool.tool_config})
            answer = await chat_session.send_message_async(final_prompt)

        # Call tools
        # DEBUG: content.parts[0] is the first step message and content.parts[1] is the function calling data that is STOPPED
        # print(answer.candidates[0].content)
        _candidates = answer.candidates[0]

        if 'function_call' in _candidates.content.parts[-1]:
            _func_call = _candidates.content.parts[-1].function_call

            # Call the function through their callables with getattr
            try:
                _result = await _Tool._tool_function(**_func_call.args)
            except (AttributeError, TypeError) as e:
                await ctx.respond("⚠️ The chat thread has a feature is not available at the moment, please reset the chat or try again in few minutes")
                # Also print the error to the console
                logging.error("slashCommands>/ask: I think I found a problem related to function calling:", e)
                return

            # send it again, and lower safety settings since each message parts may not align with safety settings and can partially block outputs and execution
            answer = await chat_session.send_message_async(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(
                            function_response = genai.protos.FunctionResponse(
                                name = _func_call.name,
                                response = {"result": _result}
                            )
                        )
                    ]
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
                }
            )

            await ctx.send(f"Used: **{_Tool.tool_human_name}**")
    
        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(answer.text) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            with open(response_file, "w+") as f:
                f.write(answer.text)
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"))
        elif len(answer.text) > 2000:
            embed = discord.Embed(
                # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
                title=str(prompt)[0:100],
                description=str(answer.text),
                color=discord.Color.random()
            )
            embed.set_author(name=self.author)
            embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(answer.text)

        # Increment the prompt count
        _prompt_count += 1
        # Also save the ChatSession.history attribute to the context history chat history key so it will be saved through pickle
        _chat_thread = jsonpickle.encode(chat_session.history, indent=4, keys=True)

        # Print context size and model info
        if append_history:
            await self.HistoryManagement.save_history(guild_id=guild_id, chat_thread=_chat_thread, prompt_count=_prompt_count)
            if verbose_logs:
                await ctx.send(inspect.cleandoc(f"""
                            > 📃 Context size: **{_prompt_count}** of {environ.get("MAX_CONTEXT_HISTORY", 20)}
                            > ✨ Model used: **{model}**
                            """))
        else:
            if verbose_logs:
                await ctx.send(f"> 📃 Responses isn't be saved\n> ✨ Model used: **{model}**")

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