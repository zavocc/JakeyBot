class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "openrouter"

        self._genai_params = {
            "max_tokens": 8192,
            "temperature": 0.7
        }

        # Multi-modal models
        self._MULTIMODAL_MODELS = (
            "gpt-4",
            "claude-3", 
            "gemini-pro-1.5",
            "gemini-flash-1.5",
            "gemini-1.5",
            "gemini-exp",
            "gemini-2.0",
            "grok-2-vision",
            "pixtral"
        )

        # Block expensive models
        self._BLOCKED_MODELS = (
            "o1-pro",
            "gpt-4.5-preview",
            "owo"
        )