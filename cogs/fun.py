from discord.ext import commands
from discord import Member, DiscordException
from os import environ
import discord
import importlib
import logging

class Fun(commands.Cog):
    """Use my fun and trivial utilities here that can help make your server more active and entertaining"""
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    async def mimic(self, ctx, user: Member, message_body: str):
        """Mimic as user!"""
        await ctx.response.defer(ephemeral=True)

        if isinstance(user, int):
            user = await self.bot.fetch_user(user)    
        avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        # Set display name depending on whether if the user joins in particular guild or in DMs to have different display names
        if ctx.guild:
            _xuser_display_name = await ctx.guild.fetch_member(user.id)
            user_name = f"{_xuser_display_name.display_name}"
        else:
            _xuser_display_name = await self.bot.fetch_user(user.id)
            user_name = f"{_xuser_display_name.display_name}"

        webhook = await ctx.channel.create_webhook(name=f"Mimic command by {self.author}")

        if not message_body:
            await ctx.respond("⚠️ Please specify a message to mimic!")
            return
        await webhook.send(content=message_body, username=user_name, avatar_url=avatar_url)
        await webhook.delete()
        
        await ctx.respond("✅ Done!")

    @mimic.error
    async def on_command_error(self, ctx: commands.Context, error: DiscordException):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadUnionArgument):
            await ctx.respond("⚠️ Please specify a valid discord user (or user id) and message to mimic!\n**Syntax:** `$mimic <user/user id> <message>`")
        elif isinstance(error, commands.CommandInvokeError) or isinstance(error, commands.MissingPermissions):
            await ctx.respond("❌ Sorry, webhooks are not enabled in this channel. Please enable webhooks in this channel to use this command.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs. Please use this command inside the guild.")
        elif isinstance(error, commands.ApplicationCommandInvokeError):
            await ctx.respond("⚠️ Please input a member")
        else:
            raise error
        
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
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
                _description = await _infer.completion([PIL.Image.open(io.BytesIO(_filedata)), "Generate image descriptions but one sentence short to describe, straight to the point"])
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

def setup(bot):
    bot.add_cog(Fun(bot))
