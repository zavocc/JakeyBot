from core.ai.assistants import Assistants
from core.ai.core import GenAIConfigDefaults
from discord.ext import commands
from os import environ
import google.generativeai as genai
import datetime
import discord
import inspect

class GenAITools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Check for gemini API keys
        if environ.get("GOOGLE_AI_TOKEN") is None or environ.get("GOOGLE_AI_TOKEN") == "INSERT_API_KEY":
            raise Exception("GOOGLE_AI_TOKEN is not configured in the dev.env file. Please configure it and try again.")

        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

   ###############################################
    # Summarize discord messages
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    @discord.option(
        "before_date",
        description="Format mm/dd/yyyy - When to read messages before the particular date",
        default=None,
    )
    @discord.option(
        "after_date",
        description="Format mm/dd/yyyy - When to read messages before the particular date",
        default=None
    )
    @discord.option(
        "around_date",
        description="Format mm/dd/yyyy - When to read messages before the particular date",
        default=None
    )
    @discord.option(
        "limit",
        description="Limit the number of messages to read - higher the limits can lead to irrelevant summary",
        min_value=5,
        max_value=50,
        default=25
    )
    async def summarize(self, ctx, before_date: str, after_date: str, around_date: str, limit: int):
        """Summarize or catch up latest messages based on the current channel"""
        await ctx.response.defer(ephemeral=True)
            
        # Do not allow message summarization if the channel is NSFW
        if ctx.channel.is_nsfw():
            await ctx.respond("❌ Sorry, I can't summarize messages in NSFW channels!")
            return

        # additional system prompt providing the user interaction context to provide personalized summaries
        _xuser_display_name = await ctx.guild.fetch_member(ctx.author.id)
        
        # Discord channel conversation context
        _current_discord_convo_context = []

        # Parse the dates
        if before_date is not None:
            before_date = datetime.datetime.strptime(before_date, '%m/%d/%Y')
        if after_date is not None:
            after_date = datetime.datetime.strptime(after_date, '%m/%d/%Y')
        if around_date is not None:
            around_date = datetime.datetime.strptime(around_date, '%m/%d/%Y')

        messages = ctx.channel.history(limit=limit, before=before_date, after=after_date, around=around_date)
        async for x in messages:
            # Handle 2000 characters limit since 4000 characters is considered spam
            if len(x.content) <= 2000:
                _current_discord_convo_context.append(inspect.cleandoc(f"""                                        
                        ---
                        # Message by: {x.author.name} at {x.created_at}

                        # Message body:
                        {x.content}

                        # Message jump link:
                        {x.jump_url}

                        # Additional information:
                        - Discord User ID: {x.author.id}
                        - Discord User Display Name: {x.author.display_name}
                        ---
                """))
            else:
                continue

        _current_discord_convo_context = "\n".join(_current_discord_convo_context)

        #################
        # MODEL
        #################
        # Initialize GenAIConfigDefaults
        genai_configs = GenAIConfigDefaults()

        # default system prompt - load assistants
        assistants_system_prompt = Assistants()

        # strain token limit output to 3024 tokens
        genai_configs.generation_config.update({"max_output_tokens": 1024})

        # set model
        model_to_use = genai.GenerativeModel(model_name=genai_configs.model_config, safety_settings=genai_configs.safety_settings_config, generation_config=genai_configs.generation_config, system_instruction=assistants_system_prompt.discord_msg_summarizer_prompt["initial_prompt"])

        summary = await model_to_use.generate_content_async(inspect.cleandoc(f"""
            You are currently interacting as a user to give personalized responses based on their activity if applicable:
                                        
            - User's nickname or display name: **{_xuser_display_name.display_name}**
            - Username (akin to user+discriminator which is deprecated format): **{ctx.author.name}**
            - User ID (this uniquely identifies the users as opposed to username/display name) **{ctx.author.id}**
                                        
            Date today is {datetime.datetime.now().strftime('%m/%d/%Y')}

            {assistants_system_prompt.discord_msg_summarizer_prompt["supplemental_prompt_format"]}

            ****************************************************
            OK, now generate summaries for me:
            ****************************************************

             {_current_discord_convo_context}
            """))

        # If arguments are given, also display the date
        _app_title = f"Summary for {ctx.channel.name}"
        if before_date is not None:
            _app_title += f" before __{before_date.date()}__"
        if after_date is not None:
            _app_title += f" after __{after_date.date()}__"
        if around_date is not None:
            _app_title += f" around __{around_date.date()}__"

        # Send message in an embed format
        embed = discord.Embed(
                title=_app_title,
                description=str(summary.text),
                color=discord.Color.random()
        )
        embed.set_author(name="Catch-up")
        embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
        await ctx.respond(embed=embed)

    # Handle errors
    @summarize.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        # Check for safety or blocked prompt errors
        _exceptions = [genai.types.StopCandidateException, ValueError]
        
        # Check if this command is executed in a guild
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this command is only to be used in a guild!")
            raise error

        # Get original exception from the DiscordException.original attribute
        error = getattr(error, "original", error)
        if any(_iter for _iter in _exceptions if isinstance(error, _iter)):
            if "time data" in str(error):
                await ctx.respond("⚠️ Sorry, I couldn't summarize messages with that date format! Please use **mm/dd/yyyy** format.")
            else:
                await ctx.respond("❌ Sorry, I can't summarize messages at the moment, I'm still learning! Please try again.")
            raise error
        else:
            await ctx.respond(f"⚠️ Uh oh! I couldn't answer your question, something happend to our end!\nHere is the logs for reference and troubleshooting:\n ```{error}```")
    
def setup(bot):
    bot.add_cog(GenAITools(bot))
