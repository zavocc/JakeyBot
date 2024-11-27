# Built in Tools
import google.generativeai as genai
import aiohttp

# Function implementations
class Tool:
    tool_human_name = "YouTube Search"
    tool_name = "youtube"
    def __init__(self, method_send, discord_bot):
        self.method_send = method_send
        self.discord_bot = discord_bot

        # YouTube
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Summarize and gather insights from a YouTube video.",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'videoid':genai.protos.Schema(type=genai.protos.Type.STRING),
                        },
                        required=['videoid']
                    )
                )
            ]
        )

        self.tool_schema_beta = {
            "functionDeclarations": [
                {
                    "name": self.tool_name,
                    "description": "Summarize and gather insights from a YouTube video.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "videoid": {
                                "type": "string"
                            }
                        },
                        "required": ["videoid"]
                    }
                }
            ]
        }

    
    async def _tool_function(self, videoid: str):
        # Using piped.video to get the video data
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("AIOHttp Client Session (MAIN/GET) not initialized, please check the bot configuration")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        async with _session.get(f"https://pipedapi.kavin.rocks/streams/{videoid}") as response:
            _json_data = await response.json()

            # Parse JSON into dict
            return {
                "title": _json_data['title'],
                "description": _json_data['description'],
                "uploader": _json_data['uploader'],
                "uploader_url": _json_data['uploaderUrl'],
                "likes": _json_data['likes'],
                "dislikes": _json_data['dislikes'],
                "views": _json_data['views']
            }
        
            
