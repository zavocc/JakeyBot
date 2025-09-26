from core.exceptions import CustomErrorMessage
from models.core import get_remix_styles_generator, get_remix_styles_async
from models.tasks.text_model_utils import get_text_models_async
from models.tasks.media.fal_ai import run_image
from discord.ext import commands
from discord import Member, DiscordException
from os import environ
import asyncio
import base64
import discord
import importlib
import logging

class AvatarTools(commands.Cog):
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
    async def remix(self, ctx: discord.ApplicationContext, style: str, user: Member = None):
        """Remix user avatar powered by Nano banana"""
        await ctx.response.defer(ephemeral=True)

        _user = await self.bot.fetch_user(user.id if user else ctx.author.id)
        if not _user.avatar:
            raise CustomErrorMessage("You don't have an avatar to be remix")
        else:
            _avatar_url = _user.avatar.url
        
        # Get the style
        _style_preprompt = await get_remix_styles_async(style=style)
        
        # Craft prompt
        _crafted_prompt = f"Transform this image provided with the style of {_style_preprompt}."

        # Parameters
        _params = {
            "prompt": _crafted_prompt,
            "image_urls": [_avatar_url],
        }

        # Run the image generation
        _imageURL = await run_image(
            model_name="gemini-25-flash-image/edit",
            aiohttp_session=self.bot.aiohttp_instance,
            send_url_only=True,
            **_params
        )

        # Create an embed
        _embed = discord.Embed(
            title="Remixed Avatar",
            description=f"Here's a remixed avatar of {_user.name}",
            color=discord.Color.random()
        )
        _embed.set_image(url=_imageURL[0])
        _embed.set_footer(text=f"Powered by Nano Banana")
        await ctx.respond(embed=_embed, ephemeral=True)

    @remix.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        _error = getattr(error, "original", error)

        if isinstance(_error, CustomErrorMessage):
            await ctx.respond(f"❌ {_error}")
        else:
            await ctx.respond("❌ Something went wrong, please try again later.")
        
        logging.error("An error has occurred while executing remix command, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(AvatarTools(bot))
