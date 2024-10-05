# type: ignore
from core.exceptions import ChatHistoryFull
import importlib
import discord

# A base template for other models
class Completions():
    def __init__(self, client_session = None, guild_id = None, 
                 model = {"model_provider": "company", "model_name": "agi-5-latest"}, 
                 db_conn = None, **kwargs):
        # This could only mean a problem has occured
        if client_session is None:
            raise AttributeError("Client session has not been started")

        # Used for tools
        if kwargs.get("_discord_bot") is not None and kwargs.get("_discord_ctx") is not None:
            self.__discord_bot: discord.Bot = kwargs.get("_discord_bot")
            self.__discord_ctx: discord.ApplicationContext = kwargs.get("_discord_ctx")

        self._Tool_use = None

        # Used for passing non-textual data into the model
        self.__discord_attachment_data = None
        self.__discord_attachment_uri = None

        # This is required - DO NOT MODIFY
        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn
        
    async def _init_tool_setup(self):
        self._Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self.__discord_bot, self.__discord_ctx)

        if self._Tool_use.tool_name == "code_execution":
            raise ValueError("Code execution is not supported in this model")

    async def multimodal_setup(self, attachment: discord.Attachment, **kwargs):
        pass


    async def completion(self, prompt, system_instruction: str = None):
       pass

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model and tools if present
        if self.__discord_bot is not None \
            and self.__discord_ctx is not None \
            and self._history_management is not None:
            await self._init_tool_setup()

        if self._Tool_use:
            if hasattr(self._Tool_use, "file_uri") and self.__discord_attachment_uri is not None:
                self._Tool_use.file_uri = self.__discord_attachment_uri
            else:
                self._Tool_use.tool_schema = None

        return {"answer":"A quick brown fox jumps over a lazy dog", "prompt_count":1+1, "chat_thread": []}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=_encoded, prompt_count=prompt_count, model_provider=self._model_provider)