# Built in Tools
import google.generativeai as genai
import aiohttp
import inspect

# Function implementations
class Tool:
    tool_human_name = "YouTube Search"
    tool_name = "youtube"
    def __init__(self, method_send):
        self.method_send = method_send

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
    
    async def _tool_function(self, videoid: str):
        # Using piped.video to get the video data
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pipedapi.kavin.rocks/streams/{videoid}") as response:
                _json_data = await response.json()

                # Parse JSON
                return inspect.cleandoc(f"""
                **Title**: {_json_data['title']}
                **Description**: {_json_data['description']}
                **Uploader**: {_json_data['uploader']}
                **Uploader URL**: {_json_data['uploaderUrl']}
                **Likes**: {_json_data['likes']}
                **Dislikes**: {_json_data['dislikes']}
                **Views**: {_json_data['views']}
                """)
