from os import environ
from pathlib import Path
import jsonpickle
import aiosqlite
import asyncio

# A class that is responsible for managing and manipulating the chat history
class HistoryManagement:
    def __init__(self, guild_id):
        self.context_history = {"prompt_history": [], "chat_history": None}
        self.history_db = environ.get("CHAT_HISTORY_DB", "chat_history.db")
        self.guild_id = guild_id

    async def initialize(self):
        # Establish connection with SQLite
        self.conn = await aiosqlite.connect(self.history_db)
        self.cursor = await self.conn.cursor()

        # Create table if not exists
        await self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                guild_id INTEGER PRIMARY KEY,
                context_history TEXT
            )
        """)
        
    async def load_history(self, check_length = False):
        # First, check if the guild id exists in the database
        _history = await self.cursor.execute("SELECT guild_id FROM chat_history WHERE guild_id = ?", (self.guild_id,))
        if (await _history.fetchone()) is not None:
            # Load the context history from the database associated with the guild_id
            await _history.execute("SELECT context_history FROM chat_history WHERE guild_id = ?", (self.guild_id,))
            self.context_history = jsonpickle.loads((await _history.fetchone())[0])
        else:
            # Create a database row for the guild id
            await self.cursor.execute("INSERT INTO chat_history (guild_id, context_history) VALUES (?, ?)", (self.guild_id, jsonpickle.dumps(self.context_history)))
            await self.conn.commit()

        if check_length:
            # Check context history size
            if len(self.context_history["prompt_history"]) >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
                raise ValueError("Maximum history reached! Clear the conversation")

    async def save_history(self):
        # Save the context history to the database
        await self.cursor.execute("UPDATE chat_history SET context_history = ? WHERE guild_id = ?", (jsonpickle.dumps(self.context_history), self.guild_id))
        await self.conn.commit()

    async def clear_history(self):
        # Remove the chat history from the database
        await self.cursor.execute("DELETE FROM chat_history WHERE guild_id = ?", (self.guild_id,))
        await self.conn.commit()