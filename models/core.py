from typing import Union
import aiofiles
import discord
import io
import logging
import os
import yaml

############################################
# ASYNC UTILITY FUNCTIONS
############################################
# Sends the AI response based on the length of the message
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

# Sets system prompt
async def set_assistant_type(assistant_name: str, type: int = 0):
    # 0 - chat_assistants
    # 1 - utility_assistants

    # Load the assistants from YAML file
    async with aiofiles.open("data/assistants.yaml", "r") as assistants:
        _assistants_data = yaml.safe_load(await assistants.read())

    if type == 0:
        _assistants_mode = _assistants_data["chat_assistants"]
    else:
        _assistants_mode = _assistants_data["utility_assistants"]

    # Return the assistant
    # We format {} to have emojis, if we use type 0
    if type == 0 and (await aiofiles.ospath.exists("emojis.yaml")):
        # The yaml format is
        # - emoji1
        # - emoji2
        # So we need to join them with newline and dash each same as yaml 
        async with aiofiles.open("emojis.yaml") as emojis_list:
            _emojis_list = "\n - ".join(yaml.safe_load(await emojis_list.read()))
            print(_emojis_list)

            if not _emojis_list:
                _emojis_list = "No emojis found"
        return _assistants_mode[assistant_name].strip().format(_emojis_list)
    else:
        return _assistants_mode[assistant_name].strip()

# For /avatar remix command
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

# For getting default chat model for async contexts
async def get_default_chat_model_async():
    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(await models.read())

    # Search through models for the first one with default: true
    for _model in _models_list:
        if _model.get("default") == True:
            logging.info("Used default chat model %s", _model.get("model_id"))
            return _model["model_alias"]
    
    # If no default model is found, raise an error
    raise ValueError("No default model found in models.yaml. Please set at least one model with 'default: true'")


# Autocomplete to fetch available models in data/models.yaml
async def get_chat_models_autocomplete(ctx: discord.AutocompleteContext):
    # ctx use is unused but required for autocomplete functions
    # so
    # TODO: add features like allowlist
    # https://docs.pycord.dev/en/v2.6.1/api/application_commands.html#discord.AutocompleteContext
    if not ctx:
        pass

    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _internal_model_data = yaml.safe_load(await models.read())

    # We pop disabled models
    _internal_model_data = [_model for _model in _internal_model_data if not _model.get("disabled", False)]

    # Return the list of models
    # Use list comprehension to build discord.OptionChoice list
    return [
        discord.OptionChoice(f"{_model['model_human_name']} - {_model['model_description']}", _model["model_alias"])
        for _model in _internal_model_data
    ]

############################################
# SYNC UTILITY FUNCTIONS
############################################
# For getting default chat model for sync contexts, e.g. database.py History init constructor to set default model when chat history is reset
# NOTE: This can only be used once, for example, initializing History class from database.py to only get default model
def get_default_chat_model():
    # Load the models list from YAML file
    with open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(models)

    # Search through models for the first one with default: true
    for _model in _models_list:
        if _model.get("default") is True:
            logging.info("Used default chat model %s", _model.get("model_id"))
            return _model["model_alias"]
    
    # If no default model is found, raise an error
    raise ValueError("No default model found in models.yaml. Please set at least one model with 'default: true'")
 
# For fetching available tools used in /agent command in cogs/ai/chat.py
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

# For /avatar remix command generator
def get_remix_styles_generator():
    # Load the tools list from YAML file
    with open("data/prompts/remix.yaml", "r") as remix_styles:
        _remix_prompts = yaml.safe_load(remix_styles)

    # Iterate through the tools and yield each as a discord.OptionChoice
    for uioptions in _remix_prompts:
        yield discord.OptionChoice(uioptions["image_style"])
