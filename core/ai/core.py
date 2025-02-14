from typing import Union
import aiofiles
import discord
import io
import yaml

class Utils:
    ###############################################
    # Method to send message dynamically based on the length of the message
    ###############################################
    @staticmethod
    async def send_ai_response(ctx: Union[discord.ApplicationContext, discord.Message], prompt: str, response: str, method_send, strip: bool = True) -> None:
        """Optimized method to send message based on the length of the message"""
        # Check if we can strip the message
        if strip:
            response = response.strip()

        # Embed the response if the response is more than 2000 characters
        # Check to see if this message is more than 2000 characters which embeds will be used for displaying the message
        if len(response) >= 4000:
            # Send the response as file
            if ctx.guild:
                if not ctx.channel.permissions_for(ctx.guild.me).attach_files:
                    await method_send("⚠️ Your message was too long to be sent please ask a follow-up question of this answer in concise format.")
                    return
                
            await method_send("⚠️ Response is too long. But, I saved your response into a markdown file", file=discord.File(io.StringIO(response), "response.md"))
        elif len(response) >= 2000:
            await method_send(
                embed=discord.Embed(
                    title=prompt.replace("\n", " ")[0:20] + "...",
                    description=response
                )
            )
        else:
            await method_send(response)


class ModelsList:
    # Must be used everytime when needing to get the models list on demand
    @staticmethod
    async def get_models_list_async():
        # Load the models list from YAML file
        async with aiofiles.open("data/models.yaml", "r") as models:
            _internal_model_data = yaml.safe_load(await models.read())

        # Iterate through the models and yield each as a discord.OptionChoice
        for model in _internal_model_data:
            yield model["model"]
        
    @staticmethod
    def get_models_list():
        # Load the models list from YAML file
        with open("data/models.yaml", "r") as models:
            _internal_model_data = yaml.safe_load(models)

        # Iterate through the models and yield each as a discord.OptionChoice
        for model in _internal_model_data:
            # Check if the model dict has hide_ui key
            if model.get("hide_ui") is not None and model.get("hide_ui") == True:
                continue

            yield discord.OptionChoice(f"{model['name']} - {model['description']}", model["model"])
        
    @staticmethod
    def get_tools_list():
        # Load the tools list from YAML file
        with open("data/tools.yaml", "r") as tools:
            _tools_list = yaml.safe_load(tools)

        # Iterate through the tools and yield each as a discord.OptionChoice
        for tool in _tools_list:
            yield discord.OptionChoice(tool["ui_name"], tool['tool_module_name'])
        