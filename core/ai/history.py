from .gridfs_ops import GridFSOps
from core.exceptions import HistoryDatabaseError
from os import environ
from pymongo import ReturnDocument
import discord as typehint_Discord
import logging
import json
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

        # GridFS Server
        self._gridfs_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(self._db, bucket_name="chat_histories")
        self._gridfs_ops = GridFSOps(self._gridfs_bucket)

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
            if "tool_use" in _existing:
                tool_use = _existing["tool_use"]
            if "default_model" in _existing:
                model = _existing["default_model"]
            if "default_openrouter_model" in _existing:
                default_openrouter_model = _existing["default_openrouter_model"]
            else:
                default_openrouter_model = None
        else:
            default_openrouter_model = None

        # Use find_one_and_update with upsert to return the document after update.
        _document = await self._collection.find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {
                "guild_id": guild_id,
                "tool_use": tool_use,
                "default_model": model,
                "default_openrouter_model": default_openrouter_model
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return _document

    async def load_history(self, guild_id: int, model_provider: str):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")
            
        _document = await self._ensure_document(guild_id)

        # Check if model_provider_{model_provider} exists in the document
        if f"chat_thread_{model_provider}" not in _document:
            await self._collection.update_one({"guild_id": guild_id}, {
                "$set": {f"chat_thread_{model_provider}": None}
            })
        
        # Otherwise we fetch and deserialize the chat thread from gridfs json
        _documentThread = _document.get(f"chat_thread_{model_provider}", None)

        try:
            if _documentThread:
                # Fetch the chat thread from GridFS
                _rawdata = await self._gridfs_ops.fetch_file(_documentThread)
                return json.loads(_rawdata.decode('utf-8'))
            else:
                return None
        except Exception as e:
            logging.error("Error fetching chat thread from GridFS: %s", e)
            raise HistoryDatabaseError("Error fetching chat thread from GridFS")

    async def save_history(self, guild_id: int, chat_thread, model_provider: str) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        _document = await self._ensure_document(guild_id)

        # Serialize the chat thread to JSON
        _serialized = json.dumps(chat_thread, ensure_ascii=False).encode('utf-8')
        try:
            # Upload the serialized chat thread to GridFS
            _file_id = await self._gridfs_ops.upload_file(guild_id, model_provider, _serialized)
        except Exception as e:
            logging.error("Error uploading chat thread to GridFS: %s", e)
            raise HistoryDatabaseError("Error uploading chat thread to GridFS")
        
        # Delete the old gridfs file associated with it if it exists
        if _document.get(f"chat_thread_{model_provider}"):
            try:
                await self._gridfs_ops.delete_file(_document[f"chat_thread_{model_provider}"])
            except Exception as e:
                logging.error("Error deleting old chat thread from GridFS: %s", e)
                raise HistoryDatabaseError("Error deleting old chat thread from GridFS")
        
        # Update the document with the new chat thread file ID
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {f"chat_thread_{model_provider}": _file_id}
        }, upsert=True)

    async def clear_history(self, guild_id: int) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")
        
        _document = await self._ensure_document(guild_id)

        # Iterate each chat_thread_{model_provider} and delete the file from GridFS if it exists
        # Checks for each keys
        for _key in _document.keys():
            # Must start with chat_thread_
            if _key.startswith("chat_thread_"):
                try:
                    if _document[_key]:
                        await self._gridfs_ops.delete_file(_document[_key])
                except Exception as e:
                    logging.error("Error deleting chat thread from GridFS: %s", e)
                    raise HistoryDatabaseError("Error deleting chat thread from GridFS")

        await self._collection.delete_one({"guild_id": guild_id})

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

