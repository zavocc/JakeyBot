from core.exceptions import ChatHistoryFull
from os import environ
import discord
import openai

class Completions:
    def __init__(self, guild_id = None, 
                 model = {"model_provider": "openai", "model_name": "gpt-4o-mini"}, 
                 db_conn = None, **kwargs):
        super().__init__()

        # Optional
        # To be set as
        # self.__discord_bot = bot
        #if kwargs.get("_discord_bot") is not None and kwargs.get("_discord_ctx") is not None:
        #    self.__discord_bot: discord.Bot = kwargs.get("_discord_bot")
        #    self.__discord_ctx: discord.ApplicationContext = kwargs.get("_discord_ctx")

        #self._Tool_use = None
        self.__discord_attachment_data = None
        #self.__discord_attachment_uri = None

        self._model_name = model["model_name"]
        self._model_provider = model["model_provider"]
        self._guild_id = guild_id
        self._history_management = db_conn

        if environ.get("OPENAI_API_KEY") is None:
            raise Exception("OpenAI API key is not configured. Please configure it and try again.")

        self._oaiclient = openai.AsyncClient(base_url=environ.get("__OAI_ENDPOINT"))
        
    #async def _init_tool_setup(self):
    #    self._Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self.__discord_bot, self.__discord_ctx)

    #    if self._Tool_use.tool_name == "code_execution":
    #        self._Tool_use.tool_schema = "code_execution"

    async def multimodal_setup(self, attachment: discord.Attachment, **kwargs):
        _attachment_data = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        # Set the attachment variable
        #self.__discord_attachment_uri = attachment.url
        self.__discord_attachment_data = _attachment_data

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model
        #if self.__discord_bot is not None and self._history_management is not None:
        #    await self._init_tool_setup()

        #if self._Tool_use:
        #    tool_config = {'function_calling_config':self._Tool_use.tool_config}

        #    if hasattr(self._Tool_use, "file_uri") and self.__discord_attachment_uri is not None:
        #        self._Tool_use.file_uri = self.__discord_attachment_uri
        #    else:
        #        tool_config = {'function_calling_config':"NONE"}
        #else:
        #    tool_config = None

        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")
        
        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": system_instruction   
            }]

        
        # Craft prompt
        _chat_thread.append(
             {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        )

        # Check if we have an attachment
        if self.__discord_attachment_data is not None:
            _chat_thread[-1]["content"].append(self.__discord_attachment_data)

        # Generate completion
        _response = await self._oaiclient.chat.completions.create(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            response_format={
                "type":"text"
            }
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": _answer
                    }
                ]
            }
        )

        return {"answer":_answer, "prompt_count":_prompt_count+1, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider)