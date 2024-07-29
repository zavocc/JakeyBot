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
            bs4 = importlib.import_module("bs4")
            ddg = importlib.import_module("duckduckgo_search")
            inspect = importlib.import_module("inspect")
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
            for url in links:
                # Perform a request
                _page_text = requests.get(url, verify=False, allow_redirects=True).text

                # Scrape with BeautifulSoup
                _scrapdata = bs4.BeautifulSoup(_page_text, 'html.parser')

                # Clean the text
                _cleantext = "\n".join([x.text for x in _scrapdata.find_all(['article', 'p'])])
                _cleantext = "\n".join([x.strip() for x in _cleantext.splitlines() if x.strip()])

                # Format
                page_contents.append(inspect.cleandoc(f"""
                
                ---
                # Page URL: {url} 
                # Page Title: {_scrapdata.title}

                # Page contents:
                ***
                {_cleantext}
                ***
                ---
                """))
        except Exception as e:
            return f"An error has occured during web browsing process, reason: {e}"

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
