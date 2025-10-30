from core.config import config
from core.exceptions import PollOffTopicRefusal
from models.core import set_assistant_type
from models.tasks.text_model_utils import fetch_text_model_config_async
from discord.ext import commands
from discord import DiscordException
import discord
import importlib
import json
import logging

class GenerativeAIFunUtils(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = config.get("discord.bot_name", "Jakey Bot")

    ###############################################
    # Polls
    ###############################################
    polls = discord.commands.SlashCommandGroup(name="polls", 
                                               description="Create polls using AI", 
                                               contexts={discord.InteractionContextType.guild})

    @polls.command()
    @discord.option(
        "prompt",
        description="What prompt should be like, use natural language to steer number of answers or type of poll",
        required=True
    )
    async def create(self, ctx: discord.ApplicationContext, prompt: str):
        """Create polls using AI"""
        await ctx.response.defer(ephemeral=False)

        # Fetch default model
        _default_model_config = await fetch_text_model_config_async()

        # Check if we can use OpenAI or Google format
        if _default_model_config["sdk"] == "openai":
            _SYM = "content"
        else:
            _SYM = "parts"

        # Base Schema
        _SCHEMA = {
            "type": "object",
            "properties": {
                "poll_description": {
                    "type": "string"
                },
                "allow_multiselect": {
                    "type": "boolean"
                },
                "poll_answers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string"
                            },
                            "emoji": {
                                "type": "string"
                            }
                        },
                        "required": ["text", "emoji"]
                    }
                },
                "poll_duration_in_hours": {
                    "type": "integer"
                },
                "deny_poll_creation_throw_err_offtopic": {
                    "type": "boolean"
                }
            },
            "required": ["poll_description", "allow_multiselect", "poll_answers", "poll_duration_in_hours", "deny_poll_creation_throw_err_offtopic"]
        }


        # Prompt for poll generation
        _prompt = [
            {
                "role": "user",
                _SYM:[
                    {
                        "text": f"Generate a poll based on the following prompt: {prompt}"
                    }
                ]
            }
        ]

        # Check if we use OpenAI to add "type": "text"
        if _default_model_config["sdk"] == "openai":
            _prompt[0][_SYM][0]["type"] = "text"

        # Init completions
        _completions = getattr(importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}"), "completion")

        _system_prompt = await set_assistant_type("discord_polls_creator_prompt", type=1)
        # Update the params to use the schema
        if _default_model_config["sdk"] == "openai":
            # Add additionalProperties to false in _SCHEMA
            _SCHEMA["additionalProperties"] = False
            _SCHEMA["properties"]["poll_answers"]["items"]["additionalProperties"] = False

            _default_model_config["model_specific_params"].update({
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "polls_create",
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

        # Poll results
        _results = json.loads(await _completions(
            prompt=_prompt,
            model_name=_default_model_config["model_id"],
            system_instruction=_system_prompt,
            client_session=getattr(self.bot, _default_model_config["client_name"], None),
            return_text=True,
            **_default_model_config["model_specific_params"]
        ))

        # Check if we can create a poll
        if _results.get("deny_poll_creation_throw_err_offtopic"):
            raise PollOffTopicRefusal

        # Create, send, and parse poll
        _poll = discord.Poll(
            question=_results["poll_description"],
            allow_multiselect=_results["allow_multiselect"],
            duration=_results["poll_duration_in_hours"]
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
    bot.add_cog(GenerativeAIFunUtils(bot))
