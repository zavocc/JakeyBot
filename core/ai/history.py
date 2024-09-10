from os import environ
import jsonpickle
import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class HistoryManagement:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.history_db = environ.get("MONGO_DB_URL")

        if not self.history_db:
            raise ConnectionError("MongoDB connection string is not set")

    async def initialize(self):
        # Establish connection with MongoDB
        self._db_conn_client = motor.motor_asyncio.AsyncIOMotorClient(self.history_db)

        # Create document if not exists
        self._db = self._db_conn_client["chat_history"]
        # Collection is under _generativeai_data_gemini
        self._collection = self._db["_jakey_data_gemini"]

        # Check if necessary fields exist
        if not await self._collection.find_one({"guild_id": self.guild_id}):
            self._collection.insert_one(
                {
                    "guild_id": self.guild_id,
                    "prompt_history": [],
                    "chat_context": None,
                    "tool_use": "code_execution"
                }
            )

    async def _get(self, key, value):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Return values
        return (await self._collection.find_one({"guild_id": self.guild_id}, {key: value}))
    
    async def _set(self, key, value):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Set values
        await self._collection.update_one(
            {"guild_id": self.guild_id},
            {"$set": {key: value}}
        )

    async def load_history(self, check_length = False):
        # Fail if initialize is not called
        if not hasattr(self, "_db") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Load the context history from the database associated with the guild_id
        _history = (await self._collection.find_one({"guild_id": self.guild_id}))["chat_context"]

        if not _history:
            return []

        if check_length:
            # Check context history size
            if type((await self._collection.find_one({"guild_id": self.guild_id}))["prompt_history"]) == list:
                if len((await self._collection.find_one({"guild_id": self.guild_id}))["prompt_history"]) >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
                    raise MemoryError("Maximum context history reached")
                
        return _history

    async def update_context(self, context):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Must be a list
        if type(context) != list:
            raise ValueError("Context data must be a list")

        # Update the chat context in the database
        await self._collection.update_one(
            {"guild_id": self.guild_id},
            {"$set": {"chat_context": context}}
        )

    async def clear_history(self):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Remove the chat history from the database
        await self._collection.delete_one({"guild_id": self.guild_id})

    async def set_config(self, tool="code_execution"):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Set the tool use configuration
        await self._collection.update_one(
            {"guild_id": self.guild_id},
            {"$set": {"tool_use": tool}}
        )
        
    async def get_config(self):
        # Fail if initialize is not called
        if not hasattr(self, "_db_conn_client") and type(self._db_conn_client) != motor.motor_asyncio.AsyncIOMotorClient:
            raise ConnectionError("Database connection not initialized, please call `initialize` method first")

        # Get the tool use configuration
        return (await self._collection.find_one({"guild_id": self.guild_id}))["tool_use"]
