import discord

class BuiltInToolDiscordStateBase:
    def __init__(self, discord_message, discord_bot):
        self.discord_message: discord.Message = discord_message
        self.discord_bot: discord.Bot = discord_bot
