from os import environ
import motor.motor_asyncio

# A class that is responsible for managing and manipulating the chat history
class HistoryManagement:
    def __init__(self, guild_id, db_conn: motor.motor_asyncio.AsyncIOMotorClient = None, chat_data = None):
        self.guild_id = guild_id
        self._db_conn = db_conn

        if db_conn is None:
            raise ConnectionError("Please set MONGO_DB_URL in dev.env")

    async def initialize(self):
        # Create a new database if it doesn't exist, access chat_history database
        self._db = self._db_conn["chat_history"]

        # _genertative_ai_gemini collection
        self._collection = self._db["_genertative_ai_gemini"]

        # create an index for the guild_id field
        await self._collection.create_index("guild_id", unique=True)

        # Create a document if it doesn't exist
        self._collection.update_one({
                "guild_id": self.guild_id,
                "prompt_history": [],
                "chat_context": None,
                "tool_use": "code_execution"
        }, upsert=True)


    async def load_history(self):
        # Initialize chat history for loading and saving
        await self.initialize()

        # Load the document
        _document = await self._collection.find_one({"guild_id": self.guild_id})
            
        # Return the prompt history and chat context
        return _document["prompt_history"], _document["chat_context"]

    async def save_history(self, chat_data, prompt_history = []):
        # Initialize chat history for loading and saving
        await self.initialize()

        # Update the document
        await self._collection.update_one({"guild_id": self.guild_id}, {
            "$set": {
                "prompt_history": prompt_history,
                "chat_context": chat_data
            }
        },
        upsert=True
        )

    async def clear_history(self):
        # Automatically initialize the database
        await self.initialize()

        # Remove the document
        await self._collection.delete_one({"guild_id": self.guild_id})

    async def set_config(self, tool="code_execution"):
        # Automatically initialize the database
        await self.initialize()

        # Update tool use
        await self._collection.update_one({"guild_id": self.guild_id}, {
            "$set": {
                "tool_use": tool
            }
        },
        upsert=True
        )

    async def get_config(self):
        await self.initialize()
        return (await self._collection.find_one({"guild_id": self.guild_id}))["tool_use"]

