# type: ignore
from core.exceptions import ChatHistoryFull
import importlib
import discord

# A base template for other models
class Completions():
    def __init__(self, guild_id = None, 
                 model_name = "agi-5-latest",
                 model_provider = "company"
                 db_conn = None, **kwargs):
        # Used for tools and interacting with the Discord APIs
        if kwargs.get("_discord_bot") is not None and kwargs.get("_discord_ctx") is not None:
            self._discord_bot: discord.Bot = kwargs.get("_discord_bot")
            self._discord_ctx: discord.ApplicationContext = kwargs.get("_discord_ctx")

        # Used for passing non-textual data into the model
        self._file_data = None # The attachment data itself (binary data, prompt, etc)
        self._file_source_url = None # To reference the source of the file

        # This is required - DO NOT MODIFY
        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn
        
    # A data must be assigned to the file_data attribute at the end
    async def input_files(self, attachment: discord.Attachment, **kwargs):
        pass

    # For non-chat completions
    async def completion(self, prompt, system_instruction: str = None):
       pass

    # For chat completions (required)
    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model and tools if present
        if self._discord_bot is not None \
            and self._discord_ctx is not None \
            and self._history_management is not None:
            _Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self._discord_bot, self._discord_ctx)

        if _Tool_use:
            if hasattr(self._Tool_use, "file_uri") and self._file_source_url is not None:
                _Tool_use.file_uri = self._file_source_url
            else:
                _Tool_use.tool_schema = None

        return {"answer":"A quick brown fox jumps over a lazy dog", "prompt_count":1+1, "chat_thread": []}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=_encoded, prompt_count=prompt_count, model_provider=self._model_provider)