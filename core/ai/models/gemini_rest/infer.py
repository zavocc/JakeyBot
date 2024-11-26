from os import environ
import aiohttp

class Completions():
    _model_provider_thread = "gemini_rest"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.5-flash-002",
                 db_conn = None):
        super().__init__()

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn

        self._api_endpoint = "https://generativelanguage.googleapis.com/v1beta"
        self._headers = {"Content-Type": "application/json"}
        self._generation_config = {
            "temperature": 1,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "text/plain"
        }

    async def chat_completion(self, prompt, system_instruction: str = None):
        _Tool = {"code_execution": {}}

        _chat_thread = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]

        # Payload
        _payload = {
            "systemInstruction": {
                "role": "user",
                "parts": [
                    {
                        "text": system_instruction
                    }
                ]
            },
            "generationConfig": self._generation_config,
            "contents": _chat_thread,
            "tools": [_Tool]
        }

        # POST request
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self._api_endpoint}/models/{self._model_name}:generateContent?key={environ.get('GEMINI_API_KEY')}",
                                    headers=self._headers,
                                    json=_payload) as response:
                _response = await response.json()

                await self._discord_method_send(_response)

        return {"answer": _response["candidates"][0]["content"]["parts"][-1]["text"], "chat_thread": None}

    async def save_to_history(self, chat_thread = None):
        raise Exception("This version is for testing purposes only, function is not implemented")