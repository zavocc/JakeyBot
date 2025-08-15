from azure.storage.blob.aio import BlobServiceClient
from discord.ext import bridge
from google import genai
from os import environ
import aiohttp
import logging
import openai

# List of services to be started, separated from main.py
# for cleanliness and modularity
class ServicesInitBot(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start_services(self):
        # Gemini API Client
        self._gemini_api_client = genai.Client(api_key=environ.get("GEMINI_API_KEY"))
        logging.info("Gemini API client initialized successfully")

        # OpenAI client for openai models
        _base_url = environ.get("OPENAI_API_ENDPOINT")

        # Check if we need to use default_query param for Azure OpenAI
        # Needed for Azure OpenAI
        if environ.get("OPENAI_USE_AZURE_OPENAI") and _base_url:
            _default_query = {"api-version": "preview"}
            logging.info("Using Azure OpenAI endpoint for OpenAI models... Using nextgen API")
        else:
            _default_query = None

        self._openai_client = openai.AsyncOpenAI(
            api_key=environ.get("OPENAI_API_KEY"),
            base_url=_base_url,
            default_query=_default_query
        )
        if _base_url:
            logging.info("OpenAI client initialized successfully with custom endpoint: %s", _base_url)
        else:
            logging.info("OpenAI client initialized successfully with default endpoint")

        # We are currently testing the next generation of Azure OpenAI
        # Simply pass this to your baseURL: https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/
        # If things break, enable the commented code below to use Azure OpenAI without the nextgen API
        # and comment the above line

        # if environ.get("OPENAI_USE_AZURE_OPENAI"):
        #     # OpenAI API endpoint must be set to Azure OpenAI endpoint
        #     if not _base_url:
        #         raise ValueError("OPENAI_API_ENDPOINT must be set when using Azure OpenAI")
        #     
        #     self._openai_client = openai.AsyncAzureOpenAI(
        #         azure_endpoint=_base_url,
        #         api_key=environ.get("OPENAI_API_KEY"),
        #         api_version="2024-12-01-preview"
        #     )
        #     logging.info("Using Azure OpenAI service for serving OpenAI models")
        # else:
        #     self._openai_client = openai.AsyncOpenAI(
        #         api_key=environ.get("OPENAI_API_KEY"),
        #         base_url=_base_url
        #     )
        #     logging.info("Using OpenAI API for serving OpenAI models")

        # OpenAI client for OpenRouter
        self._openai_client_openrouter = openai.AsyncOpenAI(
            api_key=environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        logging.info("OpenAI client for OpenRouter initialized successfully")

        # OpenAI client for Groq based models
        self._openai_client_groq = openai.AsyncOpenAI(
            api_key=environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        logging.info("OpenAI client for Groq initialized successfully")


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
