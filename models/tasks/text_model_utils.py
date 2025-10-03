from models.validation import TextTaskModelProps
import aiofiles
import discord
import logging
import yaml

async def fetch_text_model_config_async(override_model_id: str = None) -> dict:
    # Load models list
    async with aiofiles.open("data/text_models.yaml", "r") as _textmodels:
        _text_models_list = yaml.safe_load(await _textmodels.read())

    # Search through models for the first one with default: true
    _accessFirstDefaultModel = None

    # If override model ID is provided, we search associated dict and use that
    if override_model_id:
        for _model in _text_models_list:
            # Check if we have a match
            if _model.get("model_id") == override_model_id:
                logging.info("Used overridden text model %s", _model.get("model_id"))
                _accessFirstDefaultModel = _model
                break
    else:
        for _model in _text_models_list:
            if _model.get("default") == True:
                logging.info("Used default text model %s", _model.get("model_id"))
                _accessFirstDefaultModel = _model
                break
        
        if not _accessFirstDefaultModel:
            raise ValueError("No default text generation model found in text_models.yaml. Please set at least one model with 'default: true'")

    # return and validate
    return TextTaskModelProps(**_accessFirstDefaultModel).model_dump()

        
async def get_text_models_async_autocomplete(ctx: discord.AutocompleteContext):
    # ctx use is unused but required for autocomplete functions
    # so
    # TODO: add features like allowlist
    # https://docs.pycord.dev/en/v2.6.1/api/application_commands.html#discord.AutocompleteContext
    if not ctx:
        pass

    # Load the models list from YAML file
    async with aiofiles.open("data/text_models.yaml", "r") as models:
        _internal_model_data = yaml.safe_load(await models.read())

    # Return the list of models
    # Use list comprehension to build discord.OptionChoice list
    return [
        discord.OptionChoice(_model.get("model_human_name", "model_id"), _model["model_id"])
        for _model in _internal_model_data
    ]