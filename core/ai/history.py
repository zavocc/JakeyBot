from os import environ
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

    def _document_template(self, guild_id, tool_use = "code_execution"):
        return {
            "guild_id": guild_id,
            "tool_use": tool_use
        }

    async def load_history(self, guild_id, model_provider = None):
        if model_provider is None:
            raise ConnectionError("Please set a provider")

        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")
        
        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            _template = self._document_template(guild_id, 0, "code_execution")

            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": _template}, upsert=True)

        # Check if model_provider_{model_provider} exists in the document
        if f"chat_thread_{model_provider}" not in (await self._collection.find_one({"guild_id": guild_id})):
            await self._collection.update_one({"guild_id": guild_id}, {
                "$set": {
                    f"chat_thread_{model_provider}": None
                }
            })

        # Load the document
        _document = await self._collection.find_one({"guild_id": guild_id})
            
        # Return the prompt history and chat context
        return _document[f"chat_thread_{model_provider}"]

    async def save_history(self, guild_id, chat_thread, model_provider = None):
        if model_provider is None:
            raise ConnectionError("Please set a provider")

        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")

        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            _template = self._document_template(guild_id, 0, "code_execution")

            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": _template}, upsert=True)

        # Update the document
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {
                f"chat_thread_{model_provider}": chat_thread
            }
        }, upsert=True)

    async def clear_history(self, guild_id):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required and must be an integer")

        # Check if the document exists
        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            return

        # Remove the document
        await self._collection.delete_one({"guild_id": guild_id})

    async def set_config(self, guild_id, tool="code_execution", model_provider = "gemini"):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")
        
        await self.clear_history(guild_id)

        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            _template = self._document_template(guild_id, 0, tool)

            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": _template}, upsert=True)

        await self._collection.update_one({"guild_id": guild_id},{"$set": {
            "tool_use": tool
        }}, upsert=True)

    async def get_config(self, guild_id):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")
                
        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            _template = self._document_template(guild_id, 0, "code_execution")

            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": _template}, upsert=True)
            return "code_execution"

        return (await self._collection.find_one({"guild_id": guild_id}))["tool_use"]

