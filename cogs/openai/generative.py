from core.ai.openai.assistants import Assistants
from core.ai.openai.core import ModelsList
from core.ai.openai.history import History
from discord.ext import commands
from os import environ
import aiofiles
import aiofiles.os
import discord
import motor.motor_asyncio
import openai
import random

class BaseChat(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Load the database and initialize the HistoryManagement class
        # MongoDB database connection for chat history and possibly for other things
        #try:
        #    self.HistoryManagement: History = History(db_conn=motor.motor_asyncio.AsyncIOMotorClient(environ.get("MONGO_DB_URL")))
        #except Exception as e:
        #    raise e(f"Failed to connect to MongoDB: {e}...\n\nPlease set MONGO_DB_URL in dev.env")

        # Check for gemini API keys
        if environ.get("OPENAI_API_KEY") is None:
            raise Exception("OPENAI_API_KEY is not configured in the dev.env file or set environment variables. Please configure it and try again.")
        self.openai_client = openai.AsyncClient(base_url="https://models.inference.ai.azure.com", api_key=environ.get("OPENAI_API_KEY"))

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
        description="Attach your files to answer from. Supports images",
        required=False,
    )
    @discord.option(
        "model",
        description="Choose a model to use for the conversation - 4o is the default model",
        choices=ModelsList.get_models_list(),
        default="gpt-4o",
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
    async def oai_ask(self, ctx, prompt: str, attachment: discord.Attachment, model: str,
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

        ###############################################
        # File attachment processing
        ###############################################
        _xattachment = None
        # Enable multimodal support if an attachment is provided
        if attachment:
            # Set the response body
            _xattachment = {
                "type": "image_url",
                "image_url": {
                    "url": attachment.url
                }
            }
            
            # Immediately use the "used" status message to indicate that the file API is used
            if verbose_logs:
                await ctx.send(f"Used: **{attachment.filename}**")

        ###############################################
        # Answer generation
        ###############################################

        # Craft system prompt and messages
        _system_prompt = {
            "role": "system",
            "content": self._assistants_system_prompt.jakey_system_prompt
        }

        _messages = [
            _system_prompt,
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # Add multimodal prompt if necessary
        if _xattachment:
            _messages[-1]["content"].append(_xattachment)

        # Generate the response
        _response = await self.openai_client.chat.completions.create(
            model=model,
            messages=_messages
        )

        answer = _response.choices[0].message.content
    
        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(answer) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(6000,7000)}.md"
            async with aiofiles.open(response_file, "w+") as f:
                await f.write(answer)
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(response_file, "response.md"))
        elif len(answer) > 2000:
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
            await ctx.respond(answer)

        # Print context size and model info
        #if append_history:
        #    await self.HistoryManagement.save_history(guild_id=guild_id, chat_thread=_chat_thread, prompt_count=_prompt_count)
        #    if verbose_logs:
        #        await ctx.send(inspect.cleandoc(f"""
        #                   > 📃 Context size: **{_prompt_count}** of {environ.get("MAX_CONTEXT_HISTORY", 20)}
        #                    > ✨ Model used: **{model}**
        #                    > 🅰️ Chat token count: **{answer.usage_metadata.total_token_count}**
        #                    """))
        #else:
        #    if verbose_logs:
        #        await ctx.send(f"> 📃 Responses isn't be saved\n> ✨ Model used: **{model}**\n> 🅰️ Chat token count: **{answer.usage_metadata.total_token_count}**")

    # Handle all unhandled exceptions through error event, handled exceptions are currently image analysis safety settings
    @oai_ask.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        # Cooldown error
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
            return

        await ctx.respond(f"🚫 An error occurred: {error}")