# Built in Tools
import google.generativeai as genai
import importlib

class ToolsDefinitions:
    # Random Reddit
    randomreddit = genai.protos.Tool(
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

    # Web Browsing
    web_browsing = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name = "web_browsing",
                description = "Search the web from information around the world powered by DuckDuckGo",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        'query':genai.protos.Schema(type=genai.protos.Type.STRING),
                        'max_results':genai.protos.Schema(type=genai.protos.Type.NUMBER)
                    },
                    required=['query']
                )
            )
        ]
    )

    # YouTube
    youtube = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name = "youtube",
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

# Function implementations
class ToolImpl(ToolsDefinitions):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

    async def randomreddit(self, subreddit: str):
        # Fetch subreddit
        requests = importlib.import_module("requests")
        subreddit = requests.get(f"https://meme-api.com/gimme/{subreddit}").json()
        
        # Serialize objects and get the URL, image preview and title
        rdt_url = subreddit.get("postLink", "N/A")
        rdt_image = subreddit.get("url", "N/A")
        rdt_title = subreddit.get("title", "N/A")

        # Print meme information
        return f"[{rdt_title}]({rdt_image}) ([source]({rdt_url}))"
    
    async def web_browsing(self, query: str, max_results: int):
        # Limit searches upto 5 results due to context length limits
        max_results = max(max_results, 6)

        # Import required libs
        try:
            bs4 = importlib.import_module("bs4")
            ddg = importlib.import_module("duckduckgo_search")
            requests = importlib.import_module("requests")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        links = []
        # Perform search using AsyncDDGs to fully support asynchronous searches
        try:
            results = await ddg.AsyncDDGS(proxy=None).atext(query, max_results=int(max_results))
            msg = await self.ctx.send(f"🔍 Searching for **{query}**")
            # Iterate over searches with results from URL
            for urls in results:
                await msg.edit(f"➡️ Searched for {urls['title']}")
                links.append(urls["href"])
            await msg.delete()
        except Exception as e:
            return f"An error has occured, reason: {e}"
        
        # Iterate over links and scrape information
        if len(links) == 0:
            return "No results found! And no pages had been extracted"
        
        page_contents = []
        try:
            for url in links:
                # Perform a request
                _page_text = requests.get(url).text
        except Exception as e:
            return f"An error has occured during web browsing process, reason: {e}"

    
    async def youtube(self, query: str, is_youtube_link: bool):
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
