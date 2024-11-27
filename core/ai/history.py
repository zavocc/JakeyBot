from os import environ
import logging
import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class History:
    def __init__(self, db_conn: motor.motor_asyncio.AsyncIOMotorClient = None):
        self._db_conn = db_conn

        if db_conn is None:
            raise ConnectionError("Please set MONGO_DB_URL in dev.env")
        
        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn[environ.get("MONGO_DB_NAME", "chat_history_prod")]
        self._collection = self._db["db_collection"]
        logging.info(f"Connected to the database {self._db.name} and collection {self._collection.name}")

    async def _ensure_document(self, guild_id: int, model: str = "gemini::gemini-1.5-flash-002", tool_use: str = "code_execution"):
        """Ensures a document exists for the given guild_id, creates one if it doesn't exist."""
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        # Do not override tool_use and default_model if it already exists
        _existing = await self._collection.find_one({"guild_id": guild_id})
        if _existing:
            if "tool_use" in _existing:
                tool_use = _existing["tool_use"]
            if "default_model" in _existing:
                model = _existing["default_model"]

        await self._collection.update_one(
            {"guild_id": guild_id}, 
            {"$set": {
                "guild_id": guild_id,
                "tool_use": tool_use,
                "default_model": model
            }}, 
            upsert=True
        )

    async def load_history(self, guild_id, model_provider = None):
        if model_provider is None:
            raise ConnectionError("Please set a provider")
            
        await self._ensure_document(guild_id)

        # Check if model_provider_{model_provider} exists in the document
        if f"chat_thread_{model_provider}" not in (await self._collection.find_one({"guild_id": guild_id})):
            await self._collection.update_one({"guild_id": guild_id}, {
                "$set": {f"chat_thread_{model_provider}": None}
            })

        _document = await self._collection.find_one({"guild_id": guild_id})
        return _document[f"chat_thread_{model_provider}"]

    async def save_history(self, guild_id, chat_thread, model_provider = None) -> None:
        if model_provider is None:
            raise ConnectionError("Please set a provider")

        await self._ensure_document(guild_id)
        
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {f"chat_thread_{model_provider}": chat_thread}
        }, upsert=True)

    async def clear_history(self, guild_id) -> None:
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        await self._collection.delete_one({"guild_id": guild_id})

    async def set_config(self, guild_id, tool="code_execution") -> None:
        await self.clear_history(guild_id)
        await self._ensure_document(guild_id, tool)
        
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {"tool_use": tool}
        }, upsert=True)

    async def get_config(self, guild_id):
        await self._ensure_document(guild_id)
        return (await self._collection.find_one({"guild_id": guild_id}))["tool_use"]

    async def set_default_model(self, guild_id, model) -> None:
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
            logging.error(f"Error setting default model: {e}")
            raise e

    async def get_default_model(self, guild_id):
        if guild_id is None or not isinstance(guild_id, int):
            raise TypeError("guild_id is required and must be an integer")

        await self._ensure_document(guild_id)
        try:
            return (await self._collection.find_one({"guild_id": guild_id}))["default_model"]
        except Exception as e:
            logging.error(f"Error getting default model: {e}")
            raise e

