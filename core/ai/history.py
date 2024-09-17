import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class History:
    def __init__(self, guild_id, db_conn: motor.motor_asyncio.AsyncIOMotorClient = None):
        if guild_id is None:
            raise ValueError("Please provide a guild_id")   

        self.guild_id = guild_id
        self._db_conn = db_conn

        if db_conn is None:
            raise ConnectionError("Please set MONGO_DB_URL in dev.env")
        
        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn["chat_history"]

        # _genertative_ai_gemini collection
        self._collection = self._db["_genertative_ai_gemini"]

    async def initialize(self):
        # Create a document if it doesn't exist
        await self._collection.update_one({"guild_id": self.guild_id},{"$set": {
                "guild_id": self.guild_id,
                "prompt_history": [],
                "chat_thread": None,
                "tool_use": "code_execution"
        }}, upsert=True)

    async def load_history(self):
        if (await self._collection.find_one({"guild_id": self.guild_id})) is None:
            await self.initialize()

        # Load the document
        _document = await self._collection.find_one({"guild_id": self.guild_id})
            
        # Return the prompt history and chat context
        return _document["prompt_history"], _document["chat_thread"]

    async def save_history(self, chat_thread, prompt_history = []):
        # Update the document
        await self._collection.update_one({"guild_id": self.guild_id}, {
            "$set": {
                "prompt_history": prompt_history,
                "chat_thread": chat_thread
            }
        })

    async def clear_history(self):
        # Check if the document exists
        if (await self._collection.find_one({"guild_id": self.guild_id})) is None:
            return

        # Remove the document
        await self._collection.delete_one({"guild_id": self.guild_id})

    async def set_config(self, tool="code_execution"):
        if (await self._collection.find_one({"guild_id": self.guild_id})) is None:
            return (await self.initialize())

        # Update tool use
        await self._collection.update_one({"guild_id": self.guild_id}, {
            "$set": {
                "tool_use": tool
            }
        })

    async def get_config(self):
        if (await self._collection.find_one({"guild_id": self.guild_id})) is None:
            await self.initialize()
        return (await self._collection.find_one({"guild_id": self.guild_id}))["tool_use"]

