import os

import discord
from dotenv import load_dotenv

load_dotenv()
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hey!")

def main() -> None:
    print(f"Token: {os.getenv('DISCORD_TOKEN')}")
    bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token
