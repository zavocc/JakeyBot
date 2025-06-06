class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "openrouter"

        self._genai_params = {
            "max_tokens": 8192,
            "temperature": 0.7,
            "extra_body": {
                "plugins": [
                    {
                        "id": "file-parser",
                        "pdf": {
                            "engine": "native"
                        }
                    },
                    {
                        "id": "file-parser",
                        "pdf": {
                            "engine": "pdf-text"
                        }
                    }
                ]
            }
        }