from .validation import ModelProps
from core.ai.history import History
from core.exceptions import CustomErrorMessage
import aiofiles
import logging
import yaml
# Methods for generative_chat.py

# Fetch and validate models
async def fetch_model(model_alias: str) -> ModelProps:
    # Load the models list from YAML file
    async with aiofiles.open("data/models.yaml", "r") as models:
        _models_list = yaml.safe_load(await models.read())

    # Find the model dict with the matching alias
    _model_dict = next((mdl for mdl in _models_list if mdl.get("model_alias") == model_alias), None)

    if not _model_dict:
        raise CustomErrorMessage(f"⚠️ The current model is not yet available, please try another model.")

    return ModelProps(**_model_dict)

# Load chat history from thread_name
async def load_history(user_id: int, thread_name: str, db_conn: History) -> list:
    """Fetch chat history for a specific thread_name using get_key method."""
    try:
        _history = await db_conn.get_key(user_id, f"chat_thread_{thread_name}")
        return _history # Returns none for new threads
    except Exception as e:
        logging.error("Error loading history for thread_name %s, reason: %s", thread_name, e)
        return None

# Save chat history
async def save_history(user_id: int, thread_name: str, chat_thread: list, db_conn: History) -> None:
    """Save chat history for a specific thread_name using set_key method."""
    await db_conn.set_key(user_id, f"chat_thread_{thread_name}", chat_thread)