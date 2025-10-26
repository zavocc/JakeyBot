from core.config import config
from models.core import set_assistant_type
from discord.ext import commands
import aiofiles
import datetime
import discord
import inspect
import importlib
import json
import logging
import models.tasks.text_model_utils
import random

class AISummaries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = config.bot_name

   ###############################################
    # Summarize discord messages
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    @discord.option(
        "steer",
        description="Additional instruction to guide which content to focus on",
        default=None
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
        max_value=100,
        default=25
    )
    @discord.option(
        "model",
        description="Select model to be used for summarization",
        autocomplete=discord.utils.basic_autocomplete(models.tasks.text_model_utils.get_text_models_async_autocomplete),
        default=None
    )
    @commands.cooldown(1, 50, commands.BucketType.user)
    async def summarize(self, ctx, steer: str, before_date: str, after_date: str, around_date: str, max_references: int, limit: int, model: str):
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

        # Fetch default model
        _default_model_config = await models.tasks.text_model_utils.fetch_text_model_config_async(override_model_id=model)

        # Check if we can use OpenAI or Google format
        if _default_model_config["sdk"] == "openai":
            _SYM = "content"
        else:
            _SYM = "parts"

        _SCHEMA = {
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
        }

        # Prompt feed which contains the messages
        _prompt_feed = []
        
        _messages = ctx.channel.history(limit=limit, before=before_date, after=after_date, around=around_date)
        async for x in _messages:
            # Check if the message is empty, has less than 3 characters
            if len(x.content) < 3 or x.content.strip() == "":
                continue

            # Handle 2000 characters limit since 4000 characters is considered spam
            if len(x.content) <= 2000:
                # Check for mentions and replace them with the username
                for _mention in x.mentions:
                    x.content = x.content.replace(f"<@{_mention.id}>", f"(mentioned user: {_mention.display_name})")

                _D = {
                    "text": inspect.cleandoc(
                        f"""# Message by: {x.author.name} at {x.created_at}

                        # Message body:
                        {x.content}

                        # Message jump link:
                        {x.jump_url}

                        # Additional information:
                        - Discord User ID: {x.author.id}
                        - Discord User Display Name: {x.author.display_name}"""
                    )
                }

                # If it's openai client, add "type": "input_text"
                if _default_model_config["sdk"] == "openai":
                    _D["type"] = "text"

                _part = {
                    "role": "user",
                    _SYM: [_D]
                }

                _prompt_feed.append(_part)
            else:
                continue

        #################
        # MODEL
        #################
        # set model
        _completionImport = importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}")
        _completions = getattr(_completionImport, "completion")

        # Add final prompt to prompt feed
        _DZBL = {
            "text": inspect.cleandoc(
                f"""Date today is {datetime.datetime.now().strftime('%m/%d/%Y')}
                    Additional Instruction: {steer if steer is not None else 'N/A'}
                    OK, now generate summaries"""
            )
        }

        if _default_model_config["sdk"] == "openai":
            _DZBL["type"] = "text"

        _prompt_feed.append({
            "role": "user",
            _SYM: [_DZBL]
        })


        # Update the params to use the schema
        if _default_model_config["sdk"] == "openai":
            # Add additionalProperties to false in _SCHEMA
            _SCHEMA["additionalProperties"] = False
            _SCHEMA["properties"]["links"]["items"]["additionalProperties"] = False

            _default_model_config["model_specific_params"].update({
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "discord_message_summarizer",
                        "strict": True,
                        "schema": _SCHEMA
                    }
                }
            })
        else:
            _default_model_config["model_specific_params"].update({
                "response_schema": _SCHEMA,
                "response_mime_type": "application/json"
            })

        # Get client attributes
        _clientAttributes = getattr(self.bot, _default_model_config["client_name"], None)

        _summary = json.loads(await _completions(
            prompt=_prompt_feed,
            model_name=_default_model_config["model_id"],
            system_instruction=(await set_assistant_type("discord_msg_summarizer_prompt", 1)),
            client_session=_clientAttributes,
            return_text=True,
            **_default_model_config["model_specific_params"]
        ))

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
            response_file = f"{config.temp_dir}/response{random.randint(8000,9000)}.md"
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
                # Check if JUMP URL is Discord link, if not, skip it
                if "discord.com/channels" not in _links["jump_url"]:
                    continue

                if len(_embed.fields) >= max_references:
                    break
                # Truncate the description to 256 characters if it exceeds beyond that since discord wouldn't allow it
                _embed.add_field(name=_links["description"][:256], value=_links["jump_url"], inline=False)
                
            _embed.set_footer(text=f"Generated summaries powered by {_default_model_config.get('model_human_name', _default_model_config['model_id'])}")
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
        elif isinstance(_error, commands.CommandOnCooldown):
            await ctx.respond("ℹ️ Please wait for a minute before using this command again.")
        else:
            await ctx.respond("❌ Sorry, I can't summarize messages at the moment, I'm still learning! Please try again, and please try again later.")
        
        logging.error("An error has occurred while generating an summaries, reason: %s", _error, exc_info=True)

    
def setup(bot):
    bot.add_cog(AISummaries(bot))
