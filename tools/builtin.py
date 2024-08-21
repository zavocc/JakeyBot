# Built in Tools
import google.generativeai as genai
import discord
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

    # Artifacts
    artifacts = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name = "artifacts",
                description = "Create and upload meaningful files as artifacts within the conversation from code snippet, text outputs, or other textual data",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        'contents':genai.protos.Schema(type=genai.protos.Type.STRING),
                        'filename':genai.protos.Schema(type=genai.protos.Type.STRING)
                    },
                    required=['contents', 'filename']
                )
            )
        ]
    )

# Function implementations
class ToolImpl(ToolsDefinitions):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

    async def _artifacts(self, contents: str, filename: str):
        # Import required libs
        try:
            os = importlib.import_module("os")
            random = importlib.import_module("random")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"
        
        # Set the file path
        file_path = f"{os.environ.get('TEMP_DIR', 'temp')}/{random.randint(58386, 98159)}_{self.ctx.author.id}_{filename}"
        
        # Replace \n with new lines
        contents = contents.encode("utf-8").decode("unicode_escape")
        try:
            # Write the file, check if its a string and not binary
            if isinstance(contents, bytes):
                with open(file_path, "wb") as f:
                    f.write(contents)
            else:
                with open(file_path, "w") as f:
                    f.write(contents)
        except Exception as e:
            return f"An error occurred: {e}"
        
        # Send the file
        await self.ctx.send(file=discord.File(fp=file_path, filename=filename))

        # Remove the file
        os.remove(file_path)

        # Return the result
        return f"File has been sent"


    async def _randomreddit(self, subreddit: str):
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
    
    async def _youtube(self, query: str, is_youtube_link: bool):
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
