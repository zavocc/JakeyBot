# Built in Tools
import google.generativeai as genai
import importlib

# Function implementations
class Tool:
    tool_human_name = "YouTube Search"
    tool_name = "youtube"
    tool_config = "AUTO"
    def __init__(self, bot, method_send):
        self.bot = bot
        self.method_send = method_send

        # YouTube
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Search videos on YouTube",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'query':genai.protos.Schema(type=genai.protos.Type.STRING),
                            'is_youtube_link':genai.protos.Schema(type=genai.protos.Type.BOOLEAN)
                        },
                        required=['query', 'is_youtube_link']
                    )
                )
            ]
        )
    
    async def _tool_function(self, query: str, is_youtube_link: bool):
        # Limit searches 1-10 results
        #if max_results > 10 or max_results < 1:
        #    max_results = 10

        ytquery = f"ytsearch:{query}" if not is_youtube_link else query

        # Import yt_dlp
        try:
            yt_dlp = importlib.import_module("yt_dlp")
            inspect = importlib.import_module("inspect")

            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.sanitize_info(ydl.extract_info(ytquery, download=False))
        except ModuleNotFoundError:
            return "This tool is not available at the moment"
        except Exception as e:
            return f"An error occurred: {e}"
        
        # Serialize objects and get the URL, title, description, and channel
        return inspect.cleandoc(f"""
            YouTube search results, provide links as is, never use markdown hyperlinks as []():
            ---
            Title: {info['entries'][0]['title'] if not is_youtube_link else info['title']}
            Description: {info['entries'][0]['description'] if not is_youtube_link else info['description']}
            Channel URL: {info['entries'][0]['channel_url'] if not is_youtube_link else info['channel_url']}
            Publisher name: {info['entries'][0]['channel'] if not is_youtube_link else info['channel']}
            Video URL: {info['entries'][0]['webpage_url'] if not is_youtube_link else info['webpage_url']}
            Published at: {info['entries'][0]['upload_date'] if not is_youtube_link else info['upload_date']} (YYYYMMDD)
            ---
        """)
