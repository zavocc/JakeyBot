from core.ai.assistants import Assistants
from core.aimodels.gemini import Completions
from discord.ext import commands
from os import environ
import aiofiles
import datetime
import discord
import inspect
import logging
import json
import random

class GenAITools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

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
        "max_references",
        description="Determines how many references it should display - Max 10.",
        min_value=1,
        max_value=10,
        default=5
    )
    @discord.option(
        "limit",
        description="Limit the number of messages to read - higher the limits can lead to irrelevant summary",
        min_value=5,
        max_value=50,
        default=25
    )
    async def summarize(self, ctx, before_date: str, after_date: str, around_date: str, max_references: int, limit: int):
        """Summarize or catch up latest messages based on the current channel"""
        await ctx.response.defer(ephemeral=True)
            
        # Do not allow message summarization if the channel is NSFW
        if ctx.channel.is_nsfw():
            await ctx.respond("❌ Sorry, I can't summarize messages in NSFW channels!")
            return

        # Parse the dates
        if before_date is not None:
            before_date = datetime.datetime.strptime(before_date, '%m/%d/%Y')
        if after_date is not None:
            after_date = datetime.datetime.strptime(after_date, '%m/%d/%Y')
        if around_date is not None:
            around_date = datetime.datetime.strptime(around_date, '%m/%d/%Y')

        # Prompt feed which contains the messages
        _prompt_feed = [{
            "role": "user",
            "parts":[
                {
                    "text": inspect.cleandoc(
                        f"""Date today is {datetime.datetime.now().strftime('%m/%d/%Y')}
                        OK, now generate summaries for me:"""
                    )
                }
            ]
        }]
        

        _messages = ctx.channel.history(limit=limit, before=before_date, after=after_date, around=around_date)
        async for x in _messages:
            # Handle 2000 characters limit since 4000 characters is considered spam
            if len(x.content) <= 2000:
                _prompt_feed.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                            "text": inspect.cleandoc(
                                f"""# Message by: {x.author.name} at {x.created_at}

                                # Message body:
                                {x.content}

                                # Message jump link:
                                {x.jump_url}

                                # Additional information:
                                - Discord User ID: {x.author.id}
                                - Discord User Display Name: {x.author.display_name}""")
                            }
                        ]
                    }
                )
            else:
                continue

        #################
        # MODEL
        #################
        # set model
        _completions = Completions(discord_ctx=ctx, discord_bot=self.bot)
        _system_prompt = await Assistants.set_assistant_type("discord_msg_summarizer_prompt", type=1)

        # Constrain the output to JSON
        _completions._generation_config.update({
            "response_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string"
                    },
                    "links": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string"
                                },
                                "jump_url": {
                                    "type": "string"
                                }
                            },
                            "required": ["description", "jump_url"]
                        }
                    }
                },
                "required": ["summary", "links"]
            },
            "response_mime_type": "application/json",
        })

        _summary = json.loads(await _completions.completion(_prompt_feed, system_instruction=_system_prompt))

        # If arguments are given, also display the date
        _app_title = f"Summary for {ctx.channel.name}"
        if before_date is not None:
            _app_title += f" before __{before_date.date()}__"
        if after_date is not None:
            _app_title += f" after __{after_date.date()}__"
        if around_date is not None:
            _app_title += f" around __{around_date.date()}__"

        # Send message in an embed format or in markdown file if it exceeds to 4096 characters
        if len(_summary["summary"]) > 4096:
            # Send the response as file
            response_file = f"{environ.get('TEMP_DIR')}/response{random.randint(8000,9000)}.md"
            async with aiofiles.open(response_file, "a+") as f:
                await f.write(_app_title + "\n----------\n")
                await f.write(_summary["summary"])

                # Iterate over the provided links
                await f.write(f"\n\n----------\n# References\n----------\n\n")
                for _links in _summary["links"]:
                    await f.write(f"- [{_links['description']}]({_links['jump_url']})\n")
            await ctx.respond(f"Here is the summary generated for this channel", file=discord.File(response_file, "response.md"))
        else:
            _embed = discord.Embed(
                    title=_app_title,
                    description=str(_summary["summary"]),
                    color=discord.Color.random()
            )
            _embed.set_author(name="Catch-up")

            # Iterate over links and display it as field
            for _links in _summary["links"]:
                if len(_embed.fields) >= max_references:
                    break
                # Truncate the description to 256 characters if it exceeds beyond that since discord wouldn't allow it
                _embed.add_field(name=_links["description"][:256], value=_links["jump_url"], inline=False)
                
            _embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
            await ctx.respond(embed=_embed)

    # Handle errors
    @summarize.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):        
        # Check if this command is executed in a guild
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this command is only to be used in a guild!")

        # Get original exception from the DiscordException.original attribute
        _error = getattr(error, "original", error)
        if "time data" in str(_error):
            await ctx.respond("⚠️ Sorry, I couldn't summarize messages with that date format! Please use **mm/dd/yyyy** format.")
        else:
            await ctx.respond("❌ Sorry, I can't summarize messages at the moment, I'm still learning! Please try again, and please check console logs.")
        
        logging.error("An error has occurred while generating an summaries, reason: %s", _error, exc_info=True)

    
def setup(bot):
    bot.add_cog(GenAITools(bot))
