from azure.storage.blob.aio import BlobServiceClient
from discord.ext import bridge
import google.generativeai as genai # Corrected import
# from os import environ # No longer needed directly here
import aiohttp
import logging

# List of services to be started, separated from main.py
# for cleanliness and modularity
class ServicesInitBot(bridge.Bot):
    def __init__(self, *args, config_loader, **kwargs): # Added config_loader
        super().__init__(*args, **kwargs)
        self.config = config_loader # Store config instance

    async def start_services(self):
        # Gemini API Client
        gemini_api_key = self.config.get("api_providers.GEMINI_API_KEY")
        if gemini_api_key:
            self._gemini_api_client = genai.Client(api_key=gemini_api_key)
            logging.info("Gemini API client initialized successfully")
        else:
            logging.warning("GEMINI_API_KEY not found. Gemini API client not initialized.")
            self._gemini_api_client = None


        # Everything else (mostly GET requests)
        self._aiohttp_main_client_session = aiohttp.ClientSession(loop=self.loop)
        logging.info("aiohttp client session initialized successfully")

        # Azure Blob Storage Client
        azure_account_url = self.config.get("services.azure_storage.AZURE_STORAGE_ACCOUNT_URL")
        azure_conn_string = self.config.get("services.azure_storage.AZURE_STORAGE_CONNECTION_STRING")

        if azure_account_url and azure_conn_string:
            try:
                self._azure_blob_service_client = BlobServiceClient(
                    account_url=azure_account_url
                ).from_connection_string(azure_conn_string)
                logging.info("Azure Blob Storage client initialized successfully")
            except Exception as e:
                logging.error("Failed to initialize Azure Blob Storage client: %s, skipping....", e)
                self._azure_blob_service_client = None
        else:
            logging.warning("Azure storage credentials not found. Azure Blob Storage client not initialized.")
            self._azure_blob_service_client = None

    async def stop_services(self):
        # Close aiohttp client sessions
        await self._aiohttp_main_client_session.close()
        logging.info("aiohttp client session closed successfully")

        # Close Azure Blob Storage client
        if hasattr(self, "_azure_blob_service_client") and self._azure_blob_service_client:
            try:
                await self._azure_blob_service_client.close()
                logging.info("Azure Blob Storage client closed successfully")
            except Exception as e:
                logging.error("Failed to close Azure Blob Storage client: %s", e)
