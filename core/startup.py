from core.storage.azure import AzureBlobStorage
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

        # Storage Provider
        self.storage_provider = AzureBlobStorage(
            connection_string=environ.get("AZURE_STORAGE_CONNECTION_STRING"),
            container_name=environ.get("AZURE_STORAGE_CONTAINER_NAME")
        )
        logging.info("Storage provider initialized successfully")

    async def stop_services(self):
        # Close aiohttp client sessions
        await self.aiohttp_instance.close()
        logging.info("aiohttp client session closed successfully")

        # Close storage provider sessions if any
        if hasattr(self, 'storage_provider'):
            await self.storage_provider.close()
            logging.info("Storage provider session closed successfully")