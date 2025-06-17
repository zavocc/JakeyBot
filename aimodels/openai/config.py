class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "openai"

        self._genai_params = {
            "max_completion_tokens": 8192,
            "temperature": 0.7
        }