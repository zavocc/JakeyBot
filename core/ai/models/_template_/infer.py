# type: ignore
import discord

# A base template for other models
class Completions():
    # This will be used for chat history thread, feel free to change it
    _model_provider_thread = "ai_provider_company"

    def __init__(self, guild_id = None, 
                 model_name = "agi-5-latest"):
        # Used for passing non-textual data into the model
        self._file_data = None # The attachment data itself (binary data, prompt, etc)

        # This is required - DO NOT MODIFY
        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn
        
    # A data must be assigned to the file_data attribute at the end
    async def input_files(self, attachment: discord.Attachment):
        pass

    # For non-chat completions
    async def completion(self, prompt, system_instruction: str = None):
       pass

    # For chat completions (required)
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        return {"answer":"A quick brown fox jumps over a lazy dog", "chat_thread": []}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=_encoded, model_provider=self._model_provider_thread)