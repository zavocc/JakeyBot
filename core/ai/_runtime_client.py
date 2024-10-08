# TODO: To keep the OpenAI, Gemini, Mistal Client session objects stateful in one class maybe in main.py
from os import environ
import importlib
import logging

class AIClientSession:
    def __init__(self):
        # Gemini
        try:
            if not environ.get("GOOGLE_AI_TOKEN"):
                raise ValueError("Please configure GOOGLE_AI_TOKEN in dev.env")

            gemini = importlib.import_module("google.generativeai")
            gemini.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))
        except Exception as e:
            logging.error("Failed to configure Gemini API: %s\nexpect errors later", e)

        # OpenAI
        if environ.get("OPENAI_API_KEY"):
            if environ.get("AZURE_OAI_ENDPOINT"):
                self._model_prefix_openai = "azure/openai"
                logging.info("OpenAI models are configured with Azure OpenAI service endpoint and using OPENAI_API_KEY")
            else:
                self._model_prefix_openai = "openai"
                logging.info("OpenAI models are configured through OPENAI_API_KEY")
        else:
            # Check if we can use the OpenRouter keys instead
            if environ.get("OPENROUTER_API_KEY"):
                self._model_prefix_openai = "openrouter/openai"
                logging.info("OpenAI models are configured through OPENROUTER_API_KEY")
            else:
                logging.error("OpenAI models are not configured... expect errors later")

        # OpenAI o1 models
        if environ.get("OPENAI_O1_API_KEY"):
            self._model_prefix_openai_o1 = ""
            logging.info("OpenAI O1 models are configured through OPENAI_O1_API_KEY")
        else:
            # Check if we can use the OpenRouter keys instead
            if environ.get("OPENROUTER_API_KEY"):
                self._model_prefix_openai_o1 = "openrouter/openai"
                logging.info("OpenAI O1 models are configured through OPENROUTER_API_KEY")
            else:
                logging.error("OpenAI O1 models are not configured... expect errors later")

        # Mistral
        if environ.get("MISTRAL_API_KEY"):
            self._model_prefix_mistral = "mistral"
            logging.info("Mistral models are configured through MISTRAL_API_KEY")
        else:
            # Check if we can use the OpenRouter keys instead
            if environ.get("OPENROUTER_API_KEY"):
                self._model_prefix_mistral = "openrouter/mistralai"
                logging.info("Mistral models are configured through OPENROUTER_API_KEY")
            else:
                logging.error("Mistral models are not configured... expect errors later")

        # Anthropic
        if environ.get("ANTHROPIC_API_KEY"):
            self._model_prefix_anthropic = "anthropic"
            logging.info("Anthropic models are configured through ANTHROPIC_API_KEY")
        else:
            # Check if we can use the OpenRouter keys instead
            if environ.get("OPENROUTER_API_KEY"):
                self._model_prefix_anthropic = "openrouter/anthropic"
                logging.info("Anthropic models are configured through OPENROUTER_API_KEY")
            else:
                logging.error("Anthropic models are not configured... expect errors later")

        
