import os

import discord
from dotenv import load_dotenv

from .subclass import SCJakeyBot

_env_loaded = load_dotenv()
if not _env_loaded:
    raise ValueError("No .env file found")

bot = SCJakeyBot()
BOTNAME = "jakeybot"

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    _ = await ctx.respond("Hey!")

def main():
    # Traverse through cogs and load them
    for cog in os.listdir(f"src/{BOTNAME}/cogs"):
        if cog.endswith(".py"):
            _ = bot.load_extension(f"jakeybot.cogs.{cog[:-3]}")
    bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token
