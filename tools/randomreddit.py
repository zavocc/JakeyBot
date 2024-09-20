# Built in Tools
import google.generativeai as genai
import importlib

# Function implementations
class Tool:
    tool_human_name = "Random Reddit"
    tool_name = "randomreddit"
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        # Random Reddit
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = "randomreddit",
                    description = "Fetch random subreddits",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'subreddit':genai.protos.Schema(type=genai.protos.Type.STRING),
                        },
                        required=['subreddit']
                    )
                )
            ]
        )

    async def _tool_function(self, subreddit: str):
        # Fetch subreddit
        aiohttp = importlib.import_module("aiohttp")

        # GET meme-api.com
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with await session.get(f"https://meme-api.com/gimme/{subreddit}") as request:
                    subreddit = await request.json()
        except Exception as e:
            return f"An error has occured while fetching reddit, reason: {e}"
        
        # Serialize objects and get the URL, image preview and title
        rdt_url = subreddit.get("postLink", "N/A")
        rdt_image = subreddit.get("url", "N/A")
        rdt_title = subreddit.get("title", "N/A")

        # Print meme information
        return f"[{rdt_title}]({rdt_image}) ([source]({rdt_url}))"
