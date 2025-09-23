from models.validation import TextTaskModelProps
import aiofiles
import discord
import logging
import yaml

async def get_text_models_async(override_model_id: str = None) -> dict:
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

        
def get_text_models_generator():
    # Load the models list from YAML file
    with open("data/text_models.yaml", "r") as models:
        _internal_model_data = yaml.safe_load(models)

    # Iterate through the models and yield each as a discord.OptionChoice
    for model in _internal_model_data:
        yield discord.OptionChoice(model.get("model_human_name", "model_id"), model['model_id'])
