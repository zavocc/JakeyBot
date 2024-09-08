# Built in Tools
from core.ai.embeddings import GeminiDocumentRetrieval
from google_labs_html_chunker.html_chunker import HtmlChunker
import google.generativeai as genai
import asyncio
import discord
import importlib
import os
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
            ddg = importlib.import_module("duckduckgo_search")

            # Needed for some websites
            importlib.import_module("brotli")
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

                    # Format
                    page_contents.update({f"{url}": f"{_page_text}"})
    
        except Exception as e:
            return f"An error has occured during web browsing process, reason: {e}"

        # Check if page contents is zero
        if len(page_contents) == 0 and type(page_contents) != list:
            return f"No pages were scrapped and no data is provided"

        result = None
        # Perform vector similarity search
        try:
            _msgstatus = await self.ctx.send("📄 Extracting relevant details...")

            # check if we can connect to chroma server
            _chroma_http_host = os.environ.get("CHROMA_HTTP_HOST")
            _chroma_http_port = os.environ.get("CHROMA_HTTP_PORT")
            if not _chroma_http_host and not _chroma_http_port:
                return f"A chroma server is not running, I cannot perform web search"

            _chroma_client = await chromadb.AsyncHttpClient(host=_chroma_http_host, port=_chroma_http_port)

            # collection name
            _cln = f"{importlib.import_module('random').randint(50000, 60000)}_jakeybot_db_query_search"

            # create a collection
            _collection = await _chroma_client.get_or_create_collection(name=_cln)

            _chunk_size = 275
            # chunk and add documents
            async def __batch_chunker(url, docs):
                await _msgstatus.edit(f"🔍 Extracting relevant details from **{url}**")

                # chunk to 275 characters
                # returns the list of tuples of chunked documents associated with the url
                _chunked = HtmlChunker(
                    max_words_per_aggregate_passage=_chunk_size,
                    greedily_aggregate_sibling_nodes=True,
                    html_tags_to_exclude={"noscript", "script", "style"}
                ).chunk(docs)
                for ids, chunk in enumerate(_chunked):
                    await _collection.add(
                        documents=[chunk],
                        metadatas=[{"url":url}],
                        ids=[f"{url}_{ids}"]
                    )

            # tasks
            _tasks = [__batch_chunker(url, docs) for url, docs in page_contents.items()]
            await asyncio.gather(*_tasks)

            # Aggregate results, anchor queries associated with their URLs
            _result = []
            
            for url, _ in page_contents.items():
                _result.append("Result from {}:\n=======================\n{}\n=======================\n".format(
                    url, 
                    "\n".join((await _collection.query(
                            query_texts=query,
                            n_results=10,
                            where={"url": url}
                        ))["documents"][0])
                ))

            if os.environ.get("_WEB_ENABLE_DEBUG") == "1":
                print(_result, end="\n\n")
                print("\n".join(_result))

            # delete collection
            await _chroma_client.delete_collection(name=_cln)

            await _msgstatus.delete()

        except Exception as e:
            return f"An error has occured during relevance similarity step: {e}"

        if len(_result) == 0:
            return f"No pages has been extracted"

        # Send embed containing the links considered for the response
        _embed = discord.Embed(
            title="Links used for this response",
            description="\n".join(links),
            color=discord.Colour.random()
        )
        _embed.set_footer(text="Web search (powered by DuckDuckGo) is a beta feature, it cannot cross reference or verify the accuracy of the sources provided!")
        await self.ctx.send(embed=_embed)

        # Join page contents
        return f"Here is the extracted web pages aggregated based on the query {query}: \n" + "\n".join(_result)
