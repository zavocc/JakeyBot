from core.ai.assistants import Assistants
from discord.ext import commands
import aimodels._template_ as typehint_AIModelTemplate
import discord
import importlib
import io
import logging

class GeminiQuickChat(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    ###############################################
    # Ask slash command
    ###############################################
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @commands.cooldown(3, 6, commands.BucketType.user) # Add cooldown to prevent abuse
    @discord.option(
        "prompt",
        input_type=str,
        description="Ask Jakey any question",
        max_length=4096,
        required=True
    )
    async def ask(self, ctx: discord.ApplicationContext, prompt):
        """Ask Jakey any quick question"""
        await ctx.response.defer(ephemeral=True)

        _infer: typehint_AIModelTemplate.Completions = importlib.import_module(f"aimodels.gemini").Completions(
            discord_ctx=ctx,
            discord_bot=self.bot)
       
        ###############################################
        # Answer generation
        ###############################################
        _system_prompt = await Assistants.set_assistant_type("jakey_system_prompt", type=0)
        _result = await _infer.completion(prompt=prompt, system_instruction=_system_prompt)

        _system_embed = discord.Embed(
            # Truncate the title to (max 256 characters) if it exceeds beyond that since discord wouldn't allow it
            title=prompt.replace("\n", " ")[0:20] + "...",
            description=str(_result),
            color=discord.Color.random()
        )
    
        _system_embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!\nTo experience the full feature with memory, ask me in your server or in DMs by @mentioning me")

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(_result) > 4096:
            # Send the response as file
            await ctx.respond("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(io.StringIO(_result), "response.md"))
        else:
            await ctx.respond(embed=_system_embed)

    @ask.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        _error = getattr(error, "original", error)
        # Cooldown error
        if isinstance(_error, commands.CommandOnCooldown):
            await ctx.respond(f"🕒 Woah slow down!!! Please wait for few seconds before using this command again!")
        else:
            await ctx.respond(f"❌ Sorry, I couldn't answer your question at the moment, please try again later or change another model. What exactly happened: **`{type(_error).__name__}`**")

        # Log the error
        logging.error("An error has occurred while generating an answer, reason: ", exc_info=True)

def setup(bot):
    bot.add_cog(GeminiQuickChat(bot))