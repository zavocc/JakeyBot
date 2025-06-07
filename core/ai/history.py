from core.exceptions import HistoryDatabaseError
from os import environ
from pymongo import ReturnDocument
import discord as typehint_Discord
import logging
import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class History:
    def __init__(self, bot: typehint_Discord.Bot, db_conn: motor.motor_asyncio.AsyncIOMotorClient = None):
        self._db_conn = db_conn

        if db_conn is None:
            raise ConnectionError("Please set MONGO_DB_URL in dev.env")
        
        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn[environ.get("MONGO_DB_NAME", "jakey_prod_db")]
        self._collection = self._db[environ.get("MONGO_DB_COLLECTION_NAME", "jakey_prod_db_collection")]
        logging.info("Connected to the database %s and collection %s", self._db.name, self._collection.name)

        # Create task for indexing the collection
        bot.loop.create_task(self._init_indexes())

    async def _init_indexes(self):
        await self._collection.create_index([("guild_id", 1)], name="guild_id_index", background=True, unique=True)
        logging.info("Created index for guild_id")


    # Returns the document to be manipulated, creates one if it doesn't exist.
    async def _ensure_document(self, guild_id: int, model: str = "gemini::gemini-2.0-flash-001", tool_use: str = None):
        # Ensures a document exists for the given guild_id, creates one if it doesn't exist.
        # Returns the current document.
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        _existing = await self._collection.find_one({"guild_id": guild_id})
        if _existing:
            tool_use = _existing.get("tool_use", tool_use)
            default_model = _existing.get("default_model", model)
            default_openrouter_model = _existing.get("default_openrouter_model", "openai/gpt-4.1-mini")
        else:
            tool_use = tool_use
            default_model = model
            default_openrouter_model = "openai/gpt-4.1-mini"

        # Use find_one_and_update with upsert to return the document after update.
        _document = await self._collection.find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {
                "guild_id": guild_id,
                "tool_use": tool_use,
                "default_model": default_model,
                "default_openrouter_model": default_openrouter_model
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return _document
    

####################################################################################
# Chat History Management
####################################################################################

    # Load chat history
    async def load_history(self, guild_id: int, model_provider: str):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")
            
        _document = await self._ensure_document(guild_id)

        # Check if model_provider_{model_provider} exists in the document
        if f"chat_thread_{model_provider}" not in _document:
            await self._collection.update_one({"guild_id": guild_id}, {
                "$set": {f"chat_thread_{model_provider}": None}
            })
            _document[f"chat_thread_{model_provider}"] = None

        return _document[f"chat_thread_{model_provider}"]

    async def save_history(self, guild_id: int, chat_thread, model_provider: str) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        await self._ensure_document(guild_id)
        
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {f"chat_thread_{model_provider}": chat_thread}
        }, upsert=True)


    # Clear chat history
    async def clear_history(self, guild_id: int) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        await self._collection.delete_one({"guild_id": guild_id})

    # Tool configuration management
    async def set_tool_config(self, guild_id: int, tool: str = None) -> None:
        await self._ensure_document(guild_id, tool)
        
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {"tool_use": tool}
        }, upsert=True)

    async def get_tool_config(self, guild_id: int):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        _document = await self._ensure_document(guild_id)
        return _document["tool_use"]

    # Default model management
    async def set_default_model(self, guild_id: int, model: str) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        if not model or not isinstance(model, str):
            raise ValueError("Model must be a non-empty string")

        await self._ensure_document(guild_id, model=model)
        
        try:
            await self._collection.update_one(
                {"guild_id": guild_id}, 
                {"$set": {"default_model": model}},
                upsert=True
            )
        except Exception as e:
            logging.error("Error setting default model: %s", e)
            raise HistoryDatabaseError("Error setting default model")

    async def get_default_model(self, guild_id: int):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        try:
            _document = await self._ensure_document(guild_id)
            return _document["default_model"]
        except Exception as e:
            logging.error("Error getting default model: %s", e)
            raise HistoryDatabaseError("Error getting default model")
        
    # Directly set custom keys and values to the document
    async def set_key(self, guild_id: int, key: str, value) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        await self._ensure_document(guild_id)
        try:
            await self._collection.update_one(
                {"guild_id": guild_id}, 
                {"$set": {key: value}},
                upsert=True
            )
        except Exception as e:
            logging.error("Error setting keys: %s", e)
            raise HistoryDatabaseError(f"Error setting keys: {key}")
        
    # Directly get custom keys and values from the document
    async def get_key(self, guild_id: int, key: str):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        _document = await self._ensure_document(guild_id)
        try:
            return _document[key]
        except Exception as e:
            logging.error("Error getting key: %s", e)
            raise HistoryDatabaseError(f"Error getting key: {key}")

