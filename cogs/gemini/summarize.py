from core.ai.assistants import Assistants
from core.ai.core import GenAIConfigDefaults
from discord.ext import commands
from os import environ
import google.generativeai as genai
import discord

class GenAIApps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

        # Check for gemini API keys
        if environ.get("GOOGLE_AI_TOKEN") is None or environ.get("GOOGLE_AI_TOKEN") == "INSERT_API_KEY":
            raise Exception("GOOGLE_AI_TOKEN is not configured in the dev.env file. Please configure it and try again.")

        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

        # Default generative model settings
        self._genai_configs = GenAIConfigDefaults()

        # Assistants
        self._system_prompt = Assistants()

    ###############################################
    # Rephrase command
    ###############################################
    @commands.message_command(
        name="Rephrase this message",
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install},
    )
    async def rephrase(self, ctx, message: discord.Message):
        """Rephrase this message"""
        await ctx.response.defer(ephemeral=True)
        
        # Generative model settings
        model = genai.GenerativeModel(model_name=self._genai_configs.model_config, system_instruction=self._system_prompt.message_rephraser_prompt, generation_config=self._genai_configs.generation_config)
        answer = await model.generate_content_async(f"Rephrase this message:\n{str(message.content)}")

        # Send message in an embed format
        embed = discord.Embed(
                title="Rephrased Message",
                description=str(answer.text),
                color=discord.Color.random()
        )
        embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
        embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=embed)

    @rephrase.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return
        
         # Check for safety or blocked prompt errors
        _exceptions = [genai.types.BlockedPromptException, genai.types.StopCandidateException, ValueError]

        # Get original exception from the DiscordException.original attribute
        error = getattr(error, "original", error)
        if any(_iter for _iter in _exceptions if isinstance(error, _iter)):
            await ctx.respond("❌ Sorry, I couldn't rephrase that message. I'm still learning!")
        
        raise error

    ###############################################
    # Explain command
    ###############################################
    @commands.message_command(
        name="Explain this message",
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    async def explain(self, ctx, message: discord.Message):
        """Explain this message"""
        await ctx.response.defer(ephemeral=True)

        # Generative model settings
        model = genai.GenerativeModel(model_name=self._genai_configs.model_config, system_instruction=self._system_prompt.message_summarizer_prompt, generation_config=self._genai_configs.generation_config)
        answer = await model.generate_content_async(f"Explain and summarize:\n{str(message.content)}")

        # Send message in an embed format
        embed = discord.Embed(
                title="Explain this message",
                description=str(answer.text),
                color=discord.Color.random()
        )
        embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
        embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=embed)

    @explain.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return
        
         # Check for safety or blocked prompt errors
        _exceptions = [genai.types.BlockedPromptException, genai.types.StopCandidateException, ValueError]

        # Get original exception from the DiscordException.original attribute
        error = getattr(error, "original", error)
        if any(_iter for _iter in _exceptions if isinstance(error, _iter)):
            await ctx.respond("❌ Sorry, I couldn't explain that message. I'm still learning!")
        
        raise error


    ###############################################
    # Suggestions command
    ###############################################
    @commands.message_command(
        name="Suggest a response",
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    async def suggest(self, ctx, message: discord.Message):
        """Suggest a response based on this message"""
        await ctx.response.defer(ephemeral=True)

        # Generative model settings
        model = genai.GenerativeModel(model_name=self._genai_configs.model_config, system_instruction=self._system_prompt.message_suggestions_prompt, generation_config=self._genai_configs.generation_config)
        answer = await model.generate_content_async(f"Suggest a response:\n{str(message.content)}")

        # To protect privacy, send the message to the user
        # Send message in an embed format
        embed = discord.Embed(
                title="Suggested Messages",
                description=str(answer.text),
                color=discord.Color.random()
        )
        embed.set_footer(text="Responses generated by AI may not give accurate results! Double check with facts!")
        embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=embed)

    @suggest.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return
        
         # Check for safety or blocked prompt errors
        _exceptions = [genai.types.BlockedPromptException, genai.types.StopCandidateException, ValueError]

        # Get original exception from the DiscordException.original attribute
        error = getattr(error, "original", error)
        if any(_iter for _iter in _exceptions if isinstance(error, _iter)):
            await ctx.respond("❌ Sorry, this is embarrasing but I couldn't suggest good responses. I'm still learning!")
        
        raise error
    
def setup(bot):
    bot.add_cog(GenAIApps(bot))