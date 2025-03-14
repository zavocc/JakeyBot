from core.ai.assistants import Assistants
from core.aimodels.gemini import Completions
from core.exceptions import PollOffTopicRefusal
from discord.ext import commands
from discord import Member, DiscordException
from google.genai import types
from os import environ
import discord
import inspect
import json
import logging

class GeminiUtils(commands.Cog):
    """Gemini powered utilities"""
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")
        
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "user",
        description="A user to get avatar from",
        required=False
    )
    @discord.option(
        "describe",
        description="Describe the avatar",
        required=False
    )
    async def avatar(self, ctx, user: Member = None, describe: bool = False):
        """Get user avatar"""
        await ctx.response.defer(ephemeral=True)

        user = await self.bot.fetch_user(user.id if user else ctx.author.id)
        avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        # Generate image descriptions
        _description = None
        if describe:
            try:
                _filedata = None
                _mime_type = None
                # Download the image as files like
                # Maximum file size is 3MB so check it
                async with self.bot._aiohttp_main_client_session.head(avatar_url) as _response:
                    if int(_response.headers.get("Content-Length")) > 1500000:
                        raise Exception("Max file size reached")
                
                # Save it as bytes so base64 can read it
                async with self.bot._aiohttp_main_client_session.get(avatar_url) as response:
                    # Get mime type
                    _mime_type = response.headers.get("Content-Type")
                    _filedata = await response.content.read()
                
                # Check filedata
                if not _filedata:
                    raise Exception("No file data")
                
                # Generate description
                _infer = Completions(discord_ctx=ctx, discord_bot=self.bot)
                _description = await _infer.completion([
                    "Generate image descriptions but one sentence short to describe, straight to the point",
                    types.Part.from_bytes(
                        data=_filedata,
                        mime_type=_mime_type
                    )
                ])
            except Exception as e:
                logging.error("An error occurred while generating image descriptions: %s", e)
                _description = "Failed to generate image descriptions, check console for more info."

        # Embed
        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            description=_description,
            color=discord.Color.random()
        )
        embed.set_image(url=avatar_url)
        if _description: embed.set_footer(text="Using Gemini 2.0 Flash to generate descriptions, result may not be accurate")
        await ctx.respond(embed=embed, ephemeral=True)

    @avatar.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        await ctx.respond("❌ Something went wrong, please try again later.")
        logging.error("An error has occurred while executing avatar command, reason: ", exc_info=True)

    ###############################################
    # Polls
    ###############################################
    polls = discord.commands.SlashCommandGroup(name="polls", description="Create polls using AI")

    @polls.command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    @discord.option(
        "prompt",
        description="What prompt should be like, use natural language to steer number of answers or type of poll",
        required=True
    )
    @discord.option(
        "attachment",
        description="Attachment to be referenced for poll",
        required=False
    )
    async def create(self, ctx: discord.ApplicationContext, prompt: str, attachment: discord.Attachment = None):
        """Create polls using AI"""
        await ctx.response.defer(ephemeral=False)

        # Prompt feed which contains the messages
        _prompt_feed = [
            {
                "role": "user",
                "parts":[
                    {
                        "text": inspect.cleandoc(f"""
                        Generate a poll based on the following prompt:
                        {prompt}
                        """)
                    }
                ]
            }
        ]

        # Init completions
        _completions = Completions(discord_ctx=ctx, discord_bot=self.bot)

        # Attach files
        if attachment:
            await _completions.input_files(attachment=attachment)

            # Check for _completions._file_data
            if hasattr(_completions, "_file_data"):
                _prompt_feed.append(_completions._file_data)
        
        _system_prompt = await Assistants.set_assistant_type("discord_polls_creator_prompt", type=1)
        # Configured controlled response generation
        _completions._genai_params.update({
            "response_schema": {
                "type": "object",
                "properties": {
                    "poll_description": {
                        "type": "STRING"
                    },
                    "allow_multiselect": {
                        "type": "BOOLEAN"
                    },
                    "poll_answers": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "text": {
                                    "type": "STRING"
                                },
                                "emoji": {
                                    "type": "STRING"
                                }
                            },
                            "required": ["text", "emoji"]
                        }
                    },
                    "poll_duration_in_hours": {
                        "type": "INTEGER"
                    },
                    "deny_poll_creation_throw_err_offtopic": {
                        "type": "BOOLEAN"
                    }
                },
                "required": ["poll_description", "allow_multiselect", "poll_answers", "deny_poll_creation_throw_err_offtopic"]
            },
            "response_mime_type": "application/json"
        })

        # Poll results
        _results = json.loads(await _completions.completion(_prompt_feed, system_instruction=_system_prompt))

        # Check if we can create a poll
        if _results["deny_poll_creation_throw_err_offtopic"]:
            raise PollOffTopicRefusal

        # Create, send, and parse poll
        _poll = discord.Poll(
            question=_results["poll_description"],
            allow_multiselect=_results["allow_multiselect"],
            duration=_results.get("poll_duration_in_hours", 24)
        )

        # Add answers and must limit upto 10
        _answer_count_limit = 0
        for _answer in _results["poll_answers"]:
            if _answer_count_limit >= 10:
                break

            _poll.add_answer(text=_answer["text"][:55], emoji=_answer["emoji"])
            _answer_count_limit += 1

        # Send poll
        await ctx.respond(poll=_poll)

    @create.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        # Get original error
        error = getattr(error, "original", error)
        if isinstance(error, PollOffTopicRefusal):
            await ctx.respond("⚠️ Sorry, I couldn't generate a poll based on the prompt you provided, please rephrase your prompt that can be used to create a poll.")
        else:
            await ctx.respond("❌ Something went wrong while creating polls, please try again later.")
            logging.error("An error has occurred while executing create command, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(GeminiUtils(bot))
