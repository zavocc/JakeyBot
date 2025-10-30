from core.config import config
from core.exceptions import HistoryDatabaseError
from pymongo import ReturnDocument
import discord as typehint_Discord
import logging
import models.core
import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class History:
    def __init__(self, bot: typehint_Discord.Bot, conn_string):
        # Grab default model
        self.DEFAULT_MODEL = models.core.get_default_chat_model()

        # Create new connection
        self._db_conn = motor.motor_asyncio.AsyncIOMotorClient(conn_string)

        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn[config.get("mongodb.database_name", "jakey_prod_db")]
        self._collection = self._db[config.get("mongodb.collection_name", "jakey_prod_db_collection")]
        logging.info("Connected to the database %s and collection %s", self._db.name, self._collection.name)

        # Create task for indexing the collection
        bot.loop.create_task(self._init_indexes())

    # Setup indexes for the collection
    async def _init_indexes(self):
        await self._collection.create_index([("guild_id", 1)], name="guild_id_index", background=True, unique=True)
        logging.info("Created index for guild_id")

    # Type validation for guild_id
    def _normalize_guild_id(self, guild_id: int) -> str:
        if guild_id is None:
            raise TypeError("guild_id is required")
        _guild_id_str = str(guild_id)
        if not _guild_id_str.isdigit():
            raise ValueError("guild_id must be a string of digits")
        return _guild_id_str

    # Returns the document to be manipulated, creates one if it doesn't exist.
    async def _ensure_document(self, guild_id: str):
        # Check if guild_id is string
        if not isinstance(guild_id, str):
            raise TypeError("guild_id is required and must be a string")

        _existing = await self._collection.find_one({"guild_id": guild_id})
        if _existing:
            tool_use = _existing.get("tool_use", None)
            default_model = _existing.get("default_model", self.DEFAULT_MODEL)
            default_openrouter_model = _existing.get("default_openrouter_model", "openai/gpt-4.1-mini")
        else:
            tool_use = None
            default_model = self.DEFAULT_MODEL
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
# Database Management
####################################################################################
    # Directly set custom keys and values to the document
    async def set_key(self, guild_id: int, key: str, value) -> None:
        guild_id = self._normalize_guild_id(guild_id)
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
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        guild_id = self._normalize_guild_id(guild_id)
        _document = await self._ensure_document(guild_id)
        try:
            return _document.get(key, None)
        except Exception as e:
            logging.error("Error getting key: %s", e)
            raise HistoryDatabaseError(f"Error getting key: {key}")

    # Clear chat history
    async def clear_history(self, guild_id: int) -> None:
        guild_id = self._normalize_guild_id(guild_id)
        await self._collection.delete_one({"guild_id": guild_id})

