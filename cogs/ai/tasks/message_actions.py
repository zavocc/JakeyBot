from discord.ext import commands
from models.core import set_assistant_type
from models.tasks.text_model_utils import fetch_text_model_config_async
from os import environ
import discord
import importlib
import logging

class MessageActions(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.author = environ.get("BOT_NAME", "Jakey Bot")

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

        # Craft prompt
        _prompt_feed = f"Rephrase this message with variety to choose from:\n{str(message.content)}"
        # Replace mentions with the user's name
        for _mention in message.mentions:
            _prompt_feed = _prompt_feed.replace(f"<@{_mention.id}>", f"(mentions user: {_mention.display_name})")
        
        # Generative model settings
        # Get default model
        _default_model_config = await fetch_text_model_config_async()

        # Init completions
        _completions = getattr(importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}"), "completion")
        _system_prompt = await set_assistant_type("message_rephraser_prompt", type=1)
        _answer = await _completions(
            prompt=_prompt_feed,
            model_name=_default_model_config["model_id"],
            system_instruction=_system_prompt,
            client_session=getattr(self.bot, _default_model_config["client_name"], None),
            return_text=True,
            **_default_model_config["model_specific_params"]
        )

        # Send message in an embed format
        _embed = discord.Embed(
                title="Rephrased Message",
                description=str(_answer)[:4096],
                color=discord.Color.random()
        )
        _embed.set_footer(text=f"Rephrased using {_default_model_config.get('model_human_name', 'model_id')}")
        _embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=_embed)

    @rephrase.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return

        logging.error("An error has occurred while rephrasing the message, reason: ", exc_info=True)
        await ctx.respond("❌ Sorry, I couldn't rephrase that message. I'm still learning!")

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

        # Create embed
        _embed = discord.Embed(
            title="Explain this message",
            color=discord.Color.random()
        )

        # Generative model settings
        # Fetch default model
        _default_model_config = await fetch_text_model_config_async()

        _completions = getattr(importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}"), "completion")
        _system_prompt = await set_assistant_type("message_summarizer_prompt", type=1)

        # Craft prompt
        _constructed_prompt = []
        _prompt = f"Explain this Discord message:\n{str(message.content)}"
        
        # Replace mentions with the user's name
        for _mention in message.mentions:
            _prompt = _prompt.replace(f"<@{_mention.id}>", f"(mentions user: {_mention.display_name})")

        # TODO: To be enabled since we still haven't added checks if the default model is multimodal
        # Insert code snippet from file /snippet/codak.md

        # Construct the final prompt
        if _default_model_config["sdk"] == "openai":
            _constructed_prompt.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _prompt
                    }
                ]
            })
        else:
            _constructed_prompt.append({
                "role": "user",
                "parts": [
                    {
                        "text": _prompt
                    }
                ]
            })

        _answer = await _completions(
            prompt=_constructed_prompt,
            model_name=_default_model_config["model_id"],
            system_instruction=_system_prompt,
            client_session=getattr(self.bot, _default_model_config["client_name"], None),
            return_text=True,
            **_default_model_config["model_specific_params"]
        )
       
        # Send message in an embed format
        _embed.description = str(_answer)[:4096]
        _embed.set_footer(text=f"Explainers generated using {_default_model_config.get('model_human_name', 'model_id')}")
        _embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=_embed)

    @explain.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return
        
        logging.error("An error has occurred while generating message explanations, reason: ", exc_info=True)
        await ctx.respond("❌ Sorry, I couldn't explain that message. I'm still learning!")

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

        # Craft prompt
        _prompt_feed = f"Suggest a response based on this message:\n{str(message.content)}"
        # Replace mentions with the user's name
        for _mention in message.mentions:
            _prompt_feed = _prompt_feed.replace(f"<@{_mention.id}>", f"(mentions user: {_mention.display_name})")

        # Generative model settings
        # Get default model
        _default_model_config = await fetch_text_model_config_async()

        # Init completions
        _completions = getattr(importlib.import_module(f"models.tasks.text.{_default_model_config['sdk']}"), "completion")
        _system_prompt = await set_assistant_type("message_suggestions_prompt", type=1)
        _answer = await _completions(
            prompt=_prompt_feed,
            model_name=_default_model_config["model_id"],
            system_instruction=_system_prompt,
            client_session=getattr(self.bot, _default_model_config["client_name"], None),
            return_text=True,
            **_default_model_config["model_specific_params"]
        )

        # Send message in an embed format
        _embed = discord.Embed(
                title="Suggested Responses",
                description=str(_answer)[:4096],
                color=discord.Color.random()
        )
        _embed.set_footer(text=f"Suggestions generated using {_default_model_config.get('model_human_name', 'model_id')}")
        _embed.add_field(name="Referenced messages:", value=message.jump_url, inline=False)
        await ctx.respond(embed=_embed)

    @suggest.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs, please use this command inside the guild.")
            return
        
        logging.error("An error has occurred while generating message explanations, reason: ", exc_info=True)
        await ctx.respond("❌ Sorry, this is embarrasing but I couldn't suggest good responses. I'm still learning!")

def setup(bot):
    bot.add_cog(MessageActions(bot))
