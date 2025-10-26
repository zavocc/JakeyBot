from core.config import get_config, get_api_key
from discord.ext import bridge
from google import genai
import logging
import openai

# List of services to be started, separated from main.py
# for cleanliness and modularity
class SubClassBotPlugServices(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def start_services(self):
        config = get_config()
        
        # Gemini API Client
        gemini_key = get_api_key('gemini')
        if gemini_key:
            self.gemini_api_client = genai.Client(api_key=gemini_key)
            logging.info("Gemini API client initialized successfully")
        else:
            logging.warning("Gemini API key not found, Gemini features will be disabled")

        # OpenAI Client
        openai_key = get_api_key('openai')
        if openai_key:
            self.openai_client = openai.AsyncClient(api_key=openai_key)
            logging.info("OpenAI client initialized successfully")
        else:
            logging.warning("OpenAI API key not found, OpenAI features will be disabled")

        # OpenRouter Client
        openrouter_key = get_api_key('openrouter')
        if openrouter_key:
            self.openai_client_openrouter = openai.AsyncClient(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logging.info("OpenAI client for OpenRouter initialized successfully")
        else:
            logging.warning("OpenRouter API key not found, OpenRouter features will be disabled")

        # Groq Client
        groq_key = get_api_key('groq')
        if groq_key:
            self.openai_client_groq = openai.AsyncClient(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            logging.info("OpenAI client for Groq initialized successfully")
        else:
            logging.warning("Groq API key not found, Groq features will be disabled")

    async def stop_services(self):
        # Close aiohttp client sessions
        await self.aiohttp_instance.close()
        logging.info("aiohttp client session closed successfully")