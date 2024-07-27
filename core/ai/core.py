# Defaults
class GenAIConfigDefaults:
    def __init__(self):
        self.generation_config = {
            "temperature": 0.5,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 8192,
        }

        self.safety_settings_config = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]

        # Default model
        self.model_config = "gemini-1.5-flash-001"