from os import environ
from pathlib import Path
import jsonpickle
import aiosqlite

# A class that is responsible for managing and manipulating the chat history
class HistoryManagement:
    def __init__(self, guild_id):
        # Defaults
        self.context_history = {"prompt_history": [], "chat_history": None}
        self.guild_id = guild_id
        self.history_db = environ.get("CHAT_HISTORY_DB", "chat_history.db")
        self.tool_use = "code_execution"

    async def initialize(self):
        # Establish connection with SQLite
        #self.conn = await aiosqlite.connect(self.history_db)
        #self.cursor = await self.conn.cursor()

        # Create table if not exists
        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        guild_id INTEGER PRIMARY KEY,
                        context_history TEXT,
                        tool_use TEXT
                    )
                """)

                # Check if the 'tool_use' column exists
                await cursor.execute("PRAGMA table_info(chat_history)")
                columns = [column[1] for column in await cursor.fetchall()]

                # Add the 'tool_use' column if it doesn't exist
                if 'tool_use' not in columns:
                    await cursor.execute("ALTER TABLE chat_history ADD COLUMN tool_use TEXT")
                    await self.set_config()

                # check if the guild id exists in the database and set defaults
                _history = await cursor.execute("SELECT guild_id FROM chat_history WHERE guild_id = ?", (self.guild_id,))
                if await _history.fetchone() is None:
                    await _history.execute("INSERT INTO chat_history (guild_id, context_history, tool_use) VALUES (?, ?, ?)", (self.guild_id, jsonpickle.dumps(self.context_history), self.tool_use))
                    await conn.commit()

    async def load_history(self, check_length = False):
        # Load the context history from the database associated with the guild_id
        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.cursor() as cursor:
                _history = await cursor.execute("SELECT context_history FROM chat_history WHERE guild_id = ?", (self.guild_id,))
                self.context_history = jsonpickle.loads((await _history.fetchone())[0])
            
                if check_length:
                    # Check context history size
                    if len(self.context_history["prompt_history"]) >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
                        raise ValueError("Maximum history reached! Clear the conversation")

    async def save_history(self):
        # Save the context history to the database
        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE chat_history SET context_history = ? WHERE guild_id = ?", (jsonpickle.dumps(self.context_history), self.guild_id))
                await conn.commit()

    async def clear_history(self):
        # Automatically initialize the database
        await self.initialize()

        # Remove the chat history from the database
        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM chat_history WHERE guild_id = ?", (self.guild_id,))
                await conn.commit()

    async def set_config(self, tool="code_execution"):
        # Automatically initialize the database
        await self.initialize()

        self.tool_use = tool

        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.execute("SELECT guild_id FROM chat_history WHERE guild_id = ?", (self.guild_id,)) as cursor:
                await cursor.execute(
                    "UPDATE chat_history SET tool_use = ? WHERE guild_id = ?",
                    (tool, self.guild_id)
                )
                await conn.commit()

    async def get_config(self):
        # Automatically initialize the database
        await self.initialize()

        async with aiosqlite.connect(self.history_db) as conn:
            async with conn.execute("SELECT guild_id FROM chat_history WHERE guild_id = ?", (self.guild_id,)) as cursor:
                _config = await cursor.execute("SELECT tool_use FROM chat_history WHERE guild_id = ?", (self.guild_id,))
                _result = await _config.fetchone()
                if _result is not None:
                    self.tool_use = _result[0]
        
        return self.tool_use
