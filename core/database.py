from core.exceptions import HistoryDatabaseError
from os import environ
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
        self._db = self._db_conn[environ.get("MONGO_DB_NAME", "jakey_prod_db")]
        self._collection = self._db[environ.get("MONGO_DB_COLLECTION_NAME", "jakey_prod_db_collection")]
        self._checkpoint_collection = self._db["checkpoints"]
        logging.info("Connected to the database %s and collection %s", self._db.name, self._collection.name)

        # Create task for indexing the collection
        bot.loop.create_task(self._init_indexes())

    # Setup indexes for the collection
    async def _init_indexes(self):
        await self._collection.create_index([("guild_id", 1)], name="guild_id_index", background=True, unique=True)
        await self._checkpoint_collection.create_index([("guild_id", 1)], name="guild_id_index", background=True)
        await self._checkpoint_collection.create_index([("guild_id", 1), ("name", 1)], name="guild_id_name_index", background=True, unique=True)
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

####################################################################################
# Checkpoint Management
####################################################################################
    # Create a new checkpoint
    async def create_checkpoint(self, guild_id: int, name: str) -> None:
        guild_id = self._normalize_guild_id(guild_id)

        # Get the user's current data
        user_data = await self._ensure_document(guild_id)

        # Create the checkpoint document
        checkpoint_data = {
            "guild_id": guild_id,
            "name": name,
            "created_at": discord.utils.utcnow(),
            "data": user_data
        }

        # Insert the checkpoint into the checkpoint collection
        try:
            await self._checkpoint_collection.insert_one(checkpoint_data)
        except Exception as e:
            logging.error(f"Error creating checkpoint: {e}")
            raise HistoryDatabaseError(f"A checkpoint with the name '{name}' already exists.")

    # Restore a checkpoint
    async def restore_checkpoint(self, guild_id: int, name: str) -> None:
        guild_id = self._normalize_guild_id(guild_id)

        # Find the checkpoint
        checkpoint = await self._checkpoint_collection.find_one({"guild_id": guild_id, "name": name})
        if not checkpoint:
            raise HistoryDatabaseError(f"Checkpoint '{name}' not found.")

        # Get the data from the checkpoint
        user_data = checkpoint["data"]

        # Remove the original _id to avoid conflicts
        if "_id" in user_data:
            del user_data["_id"]

        # Restore the user's data, keeping the guild_id consistent
        await self._collection.replace_one({"guild_id": guild_id}, user_data, upsert=True)

    # List all checkpoints for a user
    async def list_checkpoints(self, guild_id: int):
        guild_id = self._normalize_guild_id(guild_id)

        checkpoints = self._checkpoint_collection.find({"guild_id": guild_id})
        return await checkpoints.to_list(length=None)

    # Delete a checkpoint
    async def delete_checkpoint(self, guild_id: int, name: str) -> bool:
        guild_id = self._normalize_guild_id(guild_id)

        result = await self._checkpoint_collection.delete_one({"guild_id": guild_id, "name": name})
        return result.deleted_count > 0
