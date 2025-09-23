from models.validation import TextTaskModelProps
from typing import Union
import aiofiles
import discord
import io
import logging
import os
import yaml

############################################
# ASYNC FUNCTIONS
############################################
async def send_ai_response(ctx: Union[discord.ApplicationContext, discord.Message], prompt: str, response: str, method_send, strip: bool = True) -> None:
    """Optimized method to send message based on the length of the message"""
    # Check if we can strip the message
    if strip and type(response) == str:
        response = response.strip()
    else:
        raise TypeError("The response is not a string")

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

async def get_remix_styles_async(style: str = "I'm feeling lucky"):
    # Load the tools list from YAML file
    async with aiofiles.open("data/prompts/remix.yaml", "r") as remix_styles:
        _remix_prompts = yaml.safe_load(await remix_styles.read())

    # Return when matching style is found
    # - image_style:
    #   preprompt:
    # This is the syntax of yaml so we need to iterate through the list until we find the matching style
    for styles in _remix_prompts:
        if styles["image_style"] == style:
            return styles["preprompt"]

async def get_default_chat_model_async():
    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(await models.read())

    # Search through models for the first one with default: true
    for _model in _models_list:
        if _model.get("default") is True:
            return _model["model_alias"]
    
    # If no default model is found, raise an error
    raise ValueError("No default model found in models.yaml. Please set at least one model with 'default: true'")

async def get_default_textgen_model_async() -> dict:
    # Load models list
    async with aiofiles.open("data/text_models.yaml", "r") as _textmodels:
        _text_models_list = yaml.safe_load(await _textmodels.read())

    # Search through models for the first one with default: true
    _accessFirstDefaultModel = None

    for _model in _text_models_list:
        if _model.get("default") is True:
            _accessFirstDefaultModel = _model
            break
    
    if not _accessFirstDefaultModel:
        raise ValueError("No default text generation model found in text_models.yaml. Please set at least one model with 'default: true'")

    # return and validate
    return TextTaskModelProps(**_accessFirstDefaultModel).model_dump()

############################################
# SYNC FUNCTIONS
############################################
def get_default_chat_model():
    # Load the models list from YAML file
    with open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(models)

    # Search through models for the first one with default: true
    for _model in _models_list:
        if _model.get("default") is True:
            return _model["model_alias"]
    
    # If no default model is found, raise an error
    raise ValueError("No default model found in models.yaml. Please set at least one model with 'default: true'")

def get_models_generator():
    # Load the models list from YAML file
    with open("data/models.yaml", "r") as models:
        _internal_model_data = yaml.safe_load(models)

    # Iterate through the models and yield each as a discord.OptionChoice
    for model in _internal_model_data:
        # Check if the model dict has disabled key
        if model.get("disabled") is not None and model.get("disabled") == True:
            continue

        yield discord.OptionChoice(f"{model['model_human_name']} - {model['model_description']}", model["model_alias"])
        
def get_tools_list_generator():
    _toolsPath = "tools/apis"

    _hasYieldDisableValue = False
    if not _hasYieldDisableValue:
        yield discord.OptionChoice("Disabled", "disabled")

    # Get directory names in /tools/apis except ones starting with "."
    # Then we yield each as a discord.OptionChoice
    for _tool_names in os.listdir("tools/apis"):
        # Folders starting with __pycache__ or . are not tools
        if _tool_names.startswith("__") or _tool_names.startswith("."):
            logging.info("Skipping %s because it starts with __ or .", _tool_names)
            continue

        # Check if it has manifest.yaml file
        if not os.path.isfile(f"{_toolsPath}/{_tool_names}/manifest.yaml"):
            logging.error("The tool %s does not have manifest.yaml file", _tool_names)
            continue

        # Check if we have "tool_name" in the manifest
        with open(f"{_toolsPath}/{_tool_names}/manifest.yaml", "r") as _manifest:
            _manifest_data = yaml.safe_load(_manifest)

            if not _manifest_data.get("tool_name"):
                logging.error("The tool %s does not have a tool_name", _tool_names)
                continue

        # Yield as discord.OptionChoice
        yield discord.OptionChoice(_manifest_data["tool_name"], _tool_names)


def get_remix_styles_generator():
    # Load the tools list from YAML file
    with open("data/prompts/remix.yaml", "r") as remix_styles:
        _remix_prompts = yaml.safe_load(remix_styles)

    # Iterate through the tools and yield each as a discord.OptionChoice
    for uioptions in _remix_prompts:
        yield discord.OptionChoice(uioptions["image_style"])
