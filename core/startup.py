# plugins
from plugins.storage_plugin import StoragePluginLoader

from discord.ext import bridge
from google import genai
from os import environ
import logging
import openai

# List of services to be started, separated from main.py
# for cleanliness and modularity
class SubClassBotPlugServices(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load storage plugin
        self.plugins_storage = StoragePluginLoader()

    def start_plugins(self):
        # Start storage plugin client if it has start method
        if hasattr(self.plugins_storage, 'start_storage_client'): 
            self.plugins_storage.start_storage_client()
        logging.info("Storage plugin client started successfully")

    async def stop_plugins(self):
        # Close storage plugin client if it has close method
        if hasattr(self.plugins_storage, 'close_storage_client'):
            await self.plugins_storage.close_storage_client()
        logging.info("Storage plugin client closed successfully")

    def start_services(self):
        # Gemini API Client
        self.gemini_api_client = genai.Client(api_key=environ.get("GEMINI_API_KEY"))
        logging.info("Gemini API client initialized successfully")

        # for direct OpenAI models
        self.openai_client = openai.AsyncClient(
            api_key=environ.get("OPENAI_API_KEY"),
        )

        # OpenAI client for OpenRouter
        self.openai_client_openrouter = openai.AsyncClient(
            api_key=environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        logging.info("OpenAI client for OpenRouter initialized successfully")

    async def stop_services(self):
        # Close aiohttp client sessions
        await self.aiohttp_instance.close()
        logging.info("aiohttp client session closed successfully")