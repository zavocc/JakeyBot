from core.aimodels.gemini import Completions
from discord.ext import commands
from discord import Member, DiscordException
from google.genai import types
from os import environ
import discord
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
        description="Describe the avatar using Gemini 1.5 Flash",
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
        if _description: embed.set_footer(text="Using Gemini 1.5 Flash to generate descriptions, result may not be accurate")
        await ctx.respond(embed=embed, ephemeral=True)

    @avatar.error
    async def on_application_command_error(self, ctx: commands.Context, error: DiscordException):
        await ctx.respond("⛔ Something went wrong, please check console log for details")
        logging.error("An error has occurred while executing avatar command, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(GeminiUtils(bot))
