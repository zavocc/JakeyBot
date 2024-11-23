from discord.ext import commands
from discord import Member, DiscordException
from os import environ
import discord
import importlib
import logging

class GeminiUtils(commands.Cog):
    """Gemini powered utilities"""
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
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
                # Import modules
                aiohttp = importlib.import_module("aiohttp")
                PIL = importlib.import_module("PIL")
                io = importlib.import_module("io")
                Completions = importlib.import_module("core.ai.models.gemini.infer").Completions

                _filedata = None
                # Download the image as files like
                async with aiohttp.ClientSession() as _session:
                    # Maximum file size is 3MB so check it
                    async with _session.head(avatar_url) as _response:
                        if int(_response.headers.get("Content-Length")) > 1500000:
                            raise Exception("Max file size reached")
                    
                    # Save it as bytes so io.BytesIO can read it
                    async with _session.get(avatar_url) as response:
                        _filedata = await response.read()
                
                # Check filedata
                if not _filedata:
                    raise Exception("No file data")
                
                # Generate description
                _infer = Completions()
                _description = await _infer.completion({
                    "role":"user",
                    "parts":[PIL.Image.open(io.BytesIO(_filedata)), "Generate image descriptions but one sentence short to describe, straight to the point"]
                })
            except Exception as e:
                logging.error("commands>avatar: An errored occured while generating image descriptions: %s", e)
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
    async def on_command_error(self, ctx: commands.Context, error: DiscordException):
        await ctx.respond("⛔ Something went wrong, please check console log for details")
        raise error

def setup(bot):
    bot.add_cog(GeminiUtils(bot))
