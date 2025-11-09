from discord.ext import bridge
from google import genai
from os import environ
from storage_plugins import get_storage_plugin, shutdown_storage_plugin
import logging
import openai

# List of services to be started, separated from main.py
# for cleanliness and modularity
class SubClassBotPlugServices(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start_services(self):
        # Gemini API Client
        self.gemini_api_client = genai.Client(api_key=environ.get("GEMINI_API_KEY"))
        logging.info("Gemini API client initialized successfully")

        self.openai_client = openai.AsyncClient(
            api_key=environ.get("OPENAI_API_KEY"),
        )

        # OpenAI client for OpenRouter
        self.openai_client_openrouter = openai.AsyncClient(
            api_key=environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        logging.info("OpenAI client for OpenRouter initialized successfully")

        # OpenAI client for Groq based models
        self.openai_client_groq = openai.AsyncClient(
            api_key=environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        logging.info("OpenAI client for Groq initialized successfully")

        # Storage plugin
        self.storage_plugin = await get_storage_plugin()
        self.storage_client = getattr(self.storage_plugin, "client", None)
        logging.info("Storage plugin %s initialized successfully", self.storage_plugin.name)

    async def stop_services(self):
        # Close aiohttp client sessions
        await self.aiohttp_instance.close()
        logging.info("aiohttp client session closed successfully")

        # Close storage plugin resources if any
        await shutdown_storage_plugin()
