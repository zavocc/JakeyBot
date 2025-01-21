# Built in Tools
from os import environ
from urllib.parse import urlparse
import aiohttp
import discord

# Function implementations
class Tool:
    tool_human_name = "Google Search"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "google_search",
                "description": "Search and fetch latest information, get detailed and verifiable answers with Google Search. Use Google Search to provide up-to-date and quality verifiable answers.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The query to search for, you can use search operators for more sophisticated searches"
                        },
                        "n_results": {
                            "type": "INTEGER",
                            "description": "The number of results to fetch, it's recommended to set from 1-3 for simple queries, 4-6 for queries require more corroborating sources, and 7-10 for complex queries"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "url_extractor",
                "description": "Extract URLs to summarize",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "urls": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            }
                        }
                    },
                    "required": ["urls"]
                }
            }
        ]
    
    async def _tool_function_google_search(self, query: str, n_results: int = 10):
        # Must not be above 10
        if n_results > 10:
            n_results = 10

        # Using piped.video to get the video data
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if we have CSE_SEARCH_ENGINE_CXID is set
        if not environ.get("CSE_SEARCH_ENGINE_CXID") or not environ.get("CSC_GCP_API_KEY"):
            raise ValueError("YouTube Data v3 API key not set, please go to https://console.cloud.google.com/apis/library/youtube.googleapis.com and get an API key under Credentials in API & Services")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Google Custom Search API Endpoint
        _endpoint = "https://customsearch.googleapis.com/customsearch/v1"

        # Parameters
        _params = {
            "num": n_results,
            "q": query,
            "safe": "active",
            "cx": environ.get("CSE_SEARCH_ENGINE_CXID"),
            "key": environ.get("CSC_GCP_API_KEY")
        }

        _headers = {
            "Accept": "application/json"
        }

        async with _session.get(_endpoint, params=_params, headers=_headers) as _response:
            _data = await _response.json()

            # If the Content-Type is not application/json
            if "application/json" not in _response.headers["Content-Type"]:
                raise Exception("The response from the YouTube API is not in JSON format")
            
            # If the response is not successful
            if _response.status != 200:
                raise Exception(f"Failed to fetch YouTube search results with code {_response.status}, reason: {_response.reason}")
            
        # Iterate over items list
        # Return the data as dict
        _output = [
            {
                "guidelines": "You must always provide references and format links with [Page Title](Page URL)",
                "formatting_rules": "Do not provide links as [Page URL](Page URL), always provide a title as this [Page Title](Page URL), if it doesn't just directly send the URL",
                "formatting_reason": "Now the reason for this is Discord doesn't nicely format the links if you don't provide a title",
                "results": []
            }
        ]
        for _item in _data["items"]:
            if _item["kind"] != "customsearch#result":
                continue

            _output[0]["results"].append({
                "title": _item["title"],
                "link": _item["link"],
                "excerpt": _item["snippet"]
            })

        # If the webpages list is empty
        if not _output[0]["results"]:
            return f"No results found for the given query **{query}**"

        # Embed that contains first 10 sources
        _sembed = discord.Embed(
            title="Sources with Google Search",
            color=discord.Color.random(),
        )

        # Searched
        await self.method_send(f"🔍 Searched: **{query}**")

        # Iterate description
        _desclinks = []
        for _results in _output[0]["results"]:
            if len(_desclinks) <= 10:
                _desclinks.append(f"- [{_results['title']}]({_results['link']})")
            else:
                break
        _sembed.description = "\n".join(_desclinks)

        _sembed.set_footer(text="Used Google search tool to fetch results, verify the information before using it.")
        await self.method_send(embed=_sembed)

        return _output
    
    # URL Extractor
    async def _tool_function_url_extractor(self, urls: list):
        # Must be 5 or below else error out
        if len(urls) > 5:
            raise ValueError("URLs must be 10 or below")
        
        # Ensure that URLs are http(s) and its not a localhost or private IP
        for _url in urls:
            _parsed = urlparse(_url)

            # Must be http or https
            if _parsed.scheme not in ["http", "https"]:
                raise ValueError(f"URL {_url} must be http or https")
            # Check if its a localhost or private IP
            if _parsed.hostname in ["localhost", "127.0.0.1"]:
                raise ValueError(f"URL {_url} must not be a localhost")

        # check for the aiohttp client session
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized and URL extraction cannot continue, please check the bot configuration")
        
        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Download the URLs
        _output = []
        _imsg = await self.method_send("🔍 Extracting URLs")
        for _url in urls:
            _imsg = await _imsg.edit(f"🔍 Extracting URL: **{_url}**")
            async with _session.get(_url) as _response:
                # Check if the response is successful
                if _response.status != 200:
                    _output.append({
                        "url": _url,
                        "content": f"Failed to fetch URL with status code {_response.status}"
                    })
                    continue

                # Check content length
                _content_length = _response.headers.get('Content-Length')

                # Error if there's no content length for bandwidth reasons
                if not _content_length:
                    await _imsg.delete()
                    raise ValueError("No content length found, the URL cannot be fetched")

                if _content_length and int(_content_length) > 3145728:
                    #_output.append({
                    #    "url": _url,
                    #    "content": "File too large (>3MB)"
                    #})
                    #continue
                    await _imsg.delete()
                    raise ValueError("File too large, must not exceed 3MB")

                # Read first chunk to detect binary content
                _chunk = await _response.content.read(1024)
                try:
                    # Try to decode as text
                    _chunk.decode('utf-8')
                    # If successful, read the rest
                    _data = _chunk.decode('utf-8') + (await _response.content.read()).decode('utf-8')
                    
                    # Additional binary check - looking for high concentration of null bytes
                    _null_count = _data.count('\x00')
                    if _null_count > len(_data) * 0.1:  # More than 10% null bytes
                        raise UnicodeDecodeError("High concentration of null bytes")
                        
                    _output.append({
                        "url": _url,
                        "content": _data
                    })
                except UnicodeDecodeError:
                    #_output.append({
                    #    "url": _url,
                    #    "content": "Binary content detected"
                    #})
                    if _imsg:
                        await _imsg.delete()
                    raise Exception("Binary content detected, I refuse to summarize this page for you.")

        # Delete the message
        if _imsg:
            await _imsg.delete()

        return _output



