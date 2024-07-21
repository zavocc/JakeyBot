from discord.ext import commands
from gradio_client import Client
import discord
import gradio_client

class HFGenAITools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.slash_command(
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm},
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install}
    )
    @discord.option(
        "prompt",
        description="Describe what the image should look like"
    )
    @discord.option(
        "negative_prompt",
        description="Keywords to exclude from being attributed",
        required=False
    )
    @discord.option(
        "width",
        description="Integer value to determine the width of the image",
        min_value=512,
        max_value=1344
    )
    @discord.option(
        "height",
        description="Integer value to determine the width of the image",
        min_value=512,
        max_value=1344
    )
    @discord.option(
        "guidance_scale",
        description="Integer value to determine how the model follows your prompts",
        max_value=10
    )
    @discord.option(
        "private",
        description="A boolean value whether to send this image in public"
    )
    async def imagine(self, ctx, prompt: str, 
                            negative_prompt: str = None, width: int = 1024, height: int = 1024, 
                            guidance_scale: int = 7, private: bool = False):
        """Generate images for free using Stable Diffusion 3 on HuggingFace"""
        await ctx.response.defer(ephemeral=private)
        
        # Default negative prompt to be appended
        _default_negative_prompt = "low quality, distorted, bad art, violence, sexually explicit, disturbing"

        # Create image
        try:
            result = Client("stabilityai/stable-diffusion-3-medium").predict(
                prompt=prompt,
                negative_prompt=f"{_default_negative_prompt}{', ' + negative_prompt if negative_prompt is not None else ' '}",
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                seed=0,
                randomize_seed=True,
                num_inference_steps=25,
                api_name="/infer"
            )
        except gradio_client.exceptions.AppError as e:
            raise e

        # Send the image
        await ctx.respond(f"Hi, I am **Image generator**, I can help you create images, I see you wanted **{prompt}** so I created an image for you. I hope you like it!", file=discord.File(fp=result[0]))
    
    @imagine.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        await ctx.respond("⛔ I'm sorry but theres an internal error occured while generating an image. Please try again later")

def setup(bot):
    bot.add_cog(HFGenAITools(bot))
