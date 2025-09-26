from models.core import get_remix_styles_generator, set_assistant_type
from models.tasks.text_model_utils import get_text_models_async
from core.exceptions import CustomErrorMessage, PollOffTopicRefusal
from discord.ext import commands
from discord import Member, DiscordException
from google.genai import types
from os import environ
import asyncio
import base64
import discord
import importlib
import inspect
import io
import json
import logging

class GenerativeAIFunUtils(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

    ###############################################
    # Avatar tools
    ###############################################
    avatar = discord.commands.SlashCommandGroup(
        name="avatar", description="Avatar tools",
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
        
    @avatar.command()
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
    async def show(self, ctx, user: Member = None, describe: bool = False):
        """Get user avatar"""
        await ctx.response.defer(ephemeral=True)

        _xuser = await self.bot.fetch_user(user.id if user else ctx.author.id)
        avatar_url = _xuser.avatar.url if _xuser.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        # Generate image descriptions
        _description = None
        if describe:
            try:
                _filedata = None
                _mime_type = None
                
                # Generate description
                # Fetch default model
                _default_model_config = await get_text_models_async()
                _completionImport = importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}")
                _completions = getattr(_completionImport, "completion")

                # Match symbols
                if _default_model_config["sdk"] == "openai":
                    _SYM = "content"
                else:
                    _SYM = "parts"

                # Generate description
                _strprompt = "Generate a single liner image description but one sentence short to describe, straight to the point, concise"
                
                # Check if we use OpenAI SDK or Google
                if _default_model_config["sdk"] == "openai":
                    _SYM = "content"
                    _contents = [
                        {
                            "type": "image_url",
                            "image_url": avatar_url

                        },
                        {
                            "type": "text",
                            "text": _strprompt
                        }
                    ]
                else:
                    # We download the file instead
                    # Maximum file size is 3MB so check it
                    async with self.bot.aiohttp_instance.head(avatar_url) as _response:
                        if int(_response.headers.get("Content-Length")) > 1500000:
                            raise Exception("Max file size reached")
                    
                    # Save it as bytes so base64 can read it
                    async with self.bot.aiohttp_instance.get(avatar_url) as response:
                        # Get mime type
                        _mime_type = response.headers.get("Content-Type")
                        _filedata = await response.content.read()
                    
                    # Check filedata
                    if not _filedata:
                        raise Exception("No file data")

                    _SYM = "parts"

                    # Contents
                    _contents = [
                        {
                            "text": _strprompt,
                            "inlineData": {
                                "mimeType": _mime_type,
                                "data": (await asyncio.to_thread(base64.b64encode, _filedata)).decode("utf-8")
                            }
                        }
                    ]

                _prompt = [
                    {
                        "role": "user",
                        _SYM: _contents
                    }
                ]

                if _default_model_config.get("client_name"):
                    _client_session = getattr(self.bot, _default_model_config.get("client_name"))
                else:
                    _client_session = None

                _description = await _completions(
                    prompt=_prompt,
                    model_name=_default_model_config["model_id"],
                    client_session=_client_session,
                    return_text=True
                )
            except Exception as e:
                logging.error("An error occurred while generating image descriptions: %s", e)
                if "Max file size reached" in str(e):
                    _description = "Image file size is too large, please use smaller images."
                else:
                    _description = "Failed to generate image descriptions, check console for more info."
            finally:
                # Free up memory
                if _filedata:
                    del _filedata

        # Embed
        _embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            description=_description,
            color=discord.Color.random()
        )
        _embed.set_image(url=avatar_url)
        if _description: _embed.set_footer(text=f"Using {_default_model_config.get('model_human_name', 'model_id')} to generate descriptions, result may not be accurate")
        await ctx.respond(embed=_embed, ephemeral=True)


    @show.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        await ctx.respond("❌ Something went wrong, please try again later.")
        logging.error("An error has occurred while executing avatar command, reason: ", exc_info=True)


    # Remix avatar command
    @avatar.command()
    @discord.option(
        "style",
        description="Style of avatar",
        choices=get_remix_styles_generator(),
        required=True
    )
    @discord.option(
        "user",
        description="A user to get avatar from",
        required=False
    )
    @discord.option(
        "temperature",
        description="Controls the temperature of the model, higher the temperature, more creative the output",
        required=False,
        default=0.7,
        max_value=2.0
    )
    async def remix(self, ctx: discord.ApplicationContext, style: str, user: Member = None, temperature: float = 0.7):
        """Remix user avatar using Gemini 2.0 Flash native image generation (EXPERIMENTAL)"""
        await ctx.response.defer(ephemeral=True)

        _user = await self.bot.fetch_user(user.id if user else ctx.author.id)
        if not _user.avatar:
            raise CustomErrorMessage("You don't have an avatar to be remix")
        else:
            _avatar_url = _user.avatar.url

        _filedata = None
        _mime_type = None
        # Download the image as files like
        # Maximum file size is 3MB so check it
        async with self.bot.aiohttp_instance.head(_avatar_url) as _response:
            if int(_response.headers.get("Content-Length")) > 1500000:
                raise CustomErrorMessage("Reduce the file size of the image to less than 1.5MB")
        
        # Save it as bytes so base64 can read it
        async with self.bot.aiohttp_instance.get(_avatar_url) as response:
            # Get mime type
            _mime_type = response.headers.get("Content-Type")
            _filedata = await response.content.read()
        
        # Check filedata
        if not _filedata:
            raise Exception("No file data")
        
        # Get the style
        _style_preprompt = None #await ModelsList.get_remix_styles_async(style=style)
        
        # Craft prompt
        _crafted_prompt = f"Transform this image provided with the style of {_style_preprompt}."

        #_infer = Completions(model_name=self._default_imagegen_model, discord_ctx=ctx, discord_bot=self.bot)
        _infer = None
        # Update params with image response modalities
        _infer._genai_params["response_modalities"] = ["Image", "Text"]
        _infer._genai_params["temperature"] = temperature
        _completion_data = await _infer.completion([
            "Only transform if the style requested here is different from the original image."
            "If the style is the same, DO NOT create an image, instead you must send message as 'I cannot restyle an image with already similar style'. Anyway, let's proceed",
            _crafted_prompt,
            types.Part.from_bytes(
                data=_filedata,
                mime_type=_mime_type
            )
        ], return_text=False)

        
        _imagedata = None
        for _parts in _completion_data.candidates[0].content.parts:
            if _parts.inline_data:
                if _parts.inline_data.mime_type.startswith("image"):
                    _imagedata = _parts.inline_data.data
                    break

        if not _imagedata:
            raise CustomErrorMessage("Failed to generate image, try using different styles or safe avatar images.")

        await ctx.respond("Ok, here's a remixed version of your avatar:", file=discord.File(fp=io.BytesIO(_imagedata), filename="generated_avatar.png"), ephemeral=True)

    @remix.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        _error = getattr(error, "original", error)

        if isinstance(_error, CustomErrorMessage):
            await ctx.respond(f"❌ {_error}")
        else:
            await ctx.respond("❌ Something went wrong, please try again later.")
        
        logging.error("An error has occurred while executing remix command, reason: ", exc_info=True)

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
        _default_model_config = await get_text_models_async()

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
