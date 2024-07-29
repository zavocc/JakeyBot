# Built in Tools
import google.generativeai as genai
import discord
import importlib

class ToolsDefinitions:
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


# Function implementations
class ToolImpl(ToolsDefinitions):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

    async def _web_browsing(self, query: str, max_results: int):
        # Limit searches upto 6 results due to context length limits
        max_results = min(max_results, 6)

        # Import required libs
        try:
            aiohttp = importlib.import_module("aiohttp")
            bs4 = importlib.import_module("bs4")
            ddg = importlib.import_module("duckduckgo_search")
            inspect = importlib.import_module("inspect")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        links = []
        # Perform search using AsyncDDGs to fully support asynchronous searches
        try:
            results = await ddg.AsyncDDGS(proxy=None).atext(query, max_results=int(max_results))
            msg = await self.ctx.send(f"🔍 Searching for **{query}**")
            # Iterate over searches with results from URL
            for urls in results:
                await msg.edit(f"➡️ Searched for **{urls['title']}**")
                links.append(urls["href"])
            await msg.delete()
        except Exception as e:
            return f"An error has occured, reason: {e}"
        
        # Iterate over links and scrape information
        if len(links) == 0:
            return "No results found! And no pages had been extracted"
        
        page_contents = []
        try:
            # Create ClientSession
            # https://github.com/aio-libs/aiohttp/issues/955#issuecomment-230897285
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                for url in links:
                    try:
                        # Perform a request
                        async with session.get(url, allow_redirects=True, timeout=10) as request:
                            _page_text = await request.text()
                    except Exception:
                        await self.ctx.send(f"⚠️ Failed to browse: **<{url}>**")
                        continue

                    # Scrape with BeautifulSoup
                    _scrapdata = bs4.BeautifulSoup(_page_text, 'html.parser')

                    # Find all elements and clean the text
                    _common_tags = ['p', 'li', 'ul', 'ol']
                    _common_tags.extend([f"h{i}" for i in range(1, 7)])
                    _cleantext = "\n".join([x.text for x in _scrapdata.find_all(_common_tags)])
                    _cleantext = "\n".join([x.strip() for x in _cleantext.splitlines() if x.strip()])

                    # Format
                    page_contents.append(inspect.cleandoc(f"""
                    
                    ---
                    # Page URL: {url} 
                    # Page Title: {_scrapdata.title.text}

                    # Page contents:
                    ***
                    {_cleantext}
                    ***
                    ---
                    """))
    
        except Exception as e:
            return f"An error has occured during web browsing process, reason: {e}"

        # Check if page contents is zero
        if len(page_contents) == 0:
            return f"No pages were scrapped and no data is provided"

        # Send embed containing the links considered for the response
        _embed = discord.Embed(
            title="Links considered for this response",
            description="\n".join(links),
            color=discord.Colour.random()
        )
        _embed.set_footer(text="Web search (powered by DuckDuckGo) is a beta feature, it cannot cross reference or verify the accuracy of the sources provided!")
        await self.ctx.send(embed=_embed)

        # Join page contents
        return f"Here is the extracted web pages based on the query {query}: \n" + "\n".join(page_contents)
