class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "xai"

        self._genai_params = {
            "max_tokens": 4096,
            "temperature": 0.7
        }