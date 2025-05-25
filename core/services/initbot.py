from azure.storage.blob.aio import BlobServiceClient
from discord.ext import bridge
from google import genai
from os import environ
import aiohttp
import logging

# List of services to be started, separated from main.py
# for cleanliness and modularity
class ServicesInitBot(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start_services(self):
        # Gemini API Client
        self._gemini_api_client = genai.Client(api_key=environ.get("GEMINI_API_KEY"))
        logging.info("Gemini API client initialized successfully")

        # Everything else (mostly GET requests)
        self._aiohttp_main_client_session = aiohttp.ClientSession(loop=self.loop)
        logging.info("aiohttp client session initialized successfully")

        # Azure Blob Storage Client
        try:
            self._azure_blob_service_client = BlobServiceClient(
                account_url=environ.get("AZURE_STORAGE_ACCOUNT_URL")
            ).from_connection_string(environ.get("AZURE_STORAGE_CONNECTION_STRING"))
            logging.info("Azure Blob Storage client initialized successfully")
        except Exception as e:
            logging.error("Failed to initialize Azure Blob Storage client: %s, skipping....", e)

    async def stop_services(self):
        # Close aiohttp client sessions
        await self._aiohttp_main_client_session.close()
        logging.info("aiohttp client session closed successfully")

        # Close Azure Blob Storage client
        if hasattr(self, "_azure_blob_service_client"):
            try:
                await self._azure_blob_service_client.close()
                logging.info("Azure Blob Storage client closed successfully")
            except Exception as e:
                logging.error("Failed to close Azure Blob Storage client: %s", e)
