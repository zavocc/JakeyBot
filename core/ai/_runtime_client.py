# TODO: To keep the OpenAI, Gemini, Mistal Client session objects stateful in one class maybe in main.py
from os import environ
import importlib
import logging

class AIClientSession:
    def __init__(self):
        # Gemini
        try:
            gemini = importlib.import_module("google.generativeai")
            gemini.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))
        except Exception as e:
            logging.error("Failed to configure Gemini API: %s\nexpect errors later", e)

        # OpenAI
        try:
            openai = importlib.import_module("openai")
            self._oaiclient = openai.AsyncClient(base_url=environ.get("__OAI_ENDPOINT"), api_key=environ.get("OPENAI_API_KEY"))
        except Exception as e:
            logging.error("Failed to configure OpenAI API: %s\nexpect errors later", e)

        # Mistral
        try:
            mistralai = importlib.import_module("mistralai")
            self._mistral_client = mistralai.Mistral(api_key=environ.get("MISTRAL_API_KEY"))
        except Exception as e:
            logging.error("Failed to configure Mistral API: %s\nexpect errors later", e)
