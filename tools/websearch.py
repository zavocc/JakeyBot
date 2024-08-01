# Built in Tools
from core.ai.embeddings import GeminiDocumentRetrieval
import google.generativeai as genai
import discord
import importlib
import yaml

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
            # For relevance and similarity
            chromadb = importlib.import_module("chromadb")
            bs4 = importlib.import_module("bs4")
            ddg = importlib.import_module("duckduckgo_search")
            inspect = importlib.import_module("inspect")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"

        links = []

        # Load excluded urls list
        with open("data/excluded_urls.yaml") as x:
            excluded_url_list = yaml.safe_load(x)

        # Iterate
        excluded_urls = " ".join([f"-site:{x}" for x in excluded_url_list])

        # Perform search using AsyncDDGs to fully support asynchronous searches
        try:
            results = await ddg.AsyncDDGS(proxy=None).atext(f"{query} {excluded_urls}", max_results=int(max_results))
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
        
        page_contents = {}
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

                    # extract and clean the text
                    _cleantext = _scrapdata.get_text()
                    _cleantext = "\n".join([x.strip() for x in _cleantext.splitlines() if x.strip()])

                    # Format
                    page_contents.update({f"{url}": f"{_cleantext}"})
    
        except Exception as e:
            return f"An error has occured during web browsing process, reason: {e}"

        # Check if page contents is zero
        if len(page_contents) == 0 and type(page_contents) != list:
            return f"No pages were scrapped and no data is provided"

        result = None
        # Perform vector similarity search
        try:
            _msgstatus = await self.ctx.send("📄 Extracting relevant details...")

            # non-persistent session
            _chroma_client = chromadb.Client()

            # create a collection
            _collection = _chroma_client.get_or_create_collection(name="query")

            # chunk and add documents
            for url, docs in page_contents.items():
                await _msgstatus.edit(f"🔍 Extracting relevant details from **{url}**")

                # chunk to 300 characters
                chunked = [(url, docs[i:i+350]) for i in range(0, len(docs), 250)]
                for id, (url, chunk) in enumerate(chunked):
                    _collection.add(
                        documents=[chunk],
                        ids=[f"{url}_{id}"]
                    )

            # Query
            result = _collection.query(
                query_texts=query,
                n_results=30
            )["documents"][0]

            print(result)

            # delete collection
            _chroma_client.delete_collection(name="query")

            await _msgstatus.delete()

        except Exception as e:
            return f"An error has occured during relevance similarity step: {e}"

        if result is None:
            return f"No pages has been extracted"

        # Send embed containing the links considered for the response
        _embed = discord.Embed(
            title="Links considered for this response",
            description="\n".join(links),
            color=discord.Colour.random()
        )
        _embed.set_footer(text="Web search (powered by DuckDuckGo) is a beta feature, it cannot cross reference or verify the accuracy of the sources provided!")
        await self.ctx.send(embed=_embed)

        # Join page contents
        return f"Here is the extracted web pages based on the query {query}: \n" + "\n".join(result)
