from .validation import ModelProps
from core.exceptions import CustomErrorMessage
import aiofiles
import yaml

async def fetch_model(model_alias: str) -> ModelProps:
    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(await models.read())

    # Find the model dict with the matching alias
    _model_dict = next((mdl for mdl in _models_list if mdl.get("model_alias") == model_alias), None)

    if not _model_dict:
        raise CustomErrorMessage(f"⚠️ The current model is not yet available, please try another model.")

    return ModelProps(**_model_dict)