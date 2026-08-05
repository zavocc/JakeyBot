import os

import discord
from dotenv import load_dotenv

load_dotenv()
bot = discord.Bot()
BOTNAME = "jakeybot"

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hey!")

def main():
    # Traverse through cogs and load them
    for cog in os.listdir(f"src/{BOTNAME}/cogs"):
        if cog.endswith(".py"):
            bot.load_extension(f"jakeybot.cogs.{cog[:-3]}")
    bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token
