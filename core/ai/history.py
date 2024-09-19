import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class History:
    def __init__(self, db_conn: motor.motor_asyncio.AsyncIOMotorClient = None):
        self._db_conn = db_conn

        if db_conn is None:
            raise ConnectionError("Please set MONGO_DB_URL in dev.env")
        
        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn["chat_history"]

        # _genertative_ai_gemini collection
        self._collection = self._db["_genertative_ai_gemini"]

    async def load_history(self, guild_id):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")

        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": {
                    "guild_id": guild_id,
                    "prompt_history": [],
                    "chat_thread": None,
                    "tool_use": "code_execution"
            }}, upsert=True)

        # Load the document
        _document = await self._collection.find_one({"guild_id": guild_id})
            
        # Return the prompt history and chat context
        return _document["prompt_history"], _document["chat_thread"]

    async def save_history(self, guild_id, chat_thread, prompt_history = []):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")

        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": {
                    "guild_id": guild_id,
                    "prompt_history": [],
                    "chat_thread": None,
                    "tool_use": "code_execution"
            }}, upsert=True)

        # Update the document
        await self._collection.update_one({"guild_id": guild_id}, {
            "$set": {
                "prompt_history": prompt_history,
                "chat_thread": chat_thread
            }
        })

    async def clear_history(self, guild_id):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required and must be an integer")
        
        # Check if the document exists
        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            return

        # Remove the document
        await self._collection.delete_one({"guild_id": guild_id})

    async def set_config(self, guild_id, tool="code_execution"):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")

        await self.clear_history(guild_id)
        await self._collection.update_one({"guild_id": guild_id},{"$set": {
                "guild_id": guild_id,
                "prompt_history": [],
                "chat_thread": None,
                "tool_use": tool
        }}, upsert=True)

    async def get_config(self, guild_id):
        if guild_id is None and type(guild_id) != int:
            raise TypeError("guild_id is required")
        
        if (await self._collection.find_one({"guild_id": guild_id})) is None:
            # Create a document if it doesn't exist
            await self._collection.update_one({"guild_id": guild_id},{"$set": {
                    "guild_id": guild_id,
                    "prompt_history": [],
                    "chat_thread": None,
                    "tool_use": "code_execution"
            }}, upsert=True)

            return "code_execution"

        return (await self._collection.find_one({"guild_id": guild_id}))["tool_use"]

