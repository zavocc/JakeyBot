from core.exceptions import CustomErrorMessage
from google.genai import types
import importlib
import logging

class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "google"

        self._genai_params = {
            "candidate_count": 1,
            "max_output_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "safety_settings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }