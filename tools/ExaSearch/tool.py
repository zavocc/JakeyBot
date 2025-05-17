# Built in Tools
from .manifest import ToolManifest
from os import environ
import aiohttp
import discord

# Function implementations
class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()

        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def _tool_function_web_search(self, query: str = None, searchType: str = "auto", numResults: int = 5, includeDomains: list = None, excludeDomains: list = None, includeText: list = None, excludeText: list = None, showHighlights: bool = False, showSummary: bool = False):
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized and web browsing cannot continue, please check the bot configuration")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Bing Subscription Key
        if not environ.get("EXA_AI_KEY"):
            raise ValueError("EXA_AI_KEY key not set")
        
        _header = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": environ.get("EXA_AI_KEY")
        }
        
        # Construct params
        _params = {
            "query": query,
            "type": searchType,
            "numResults": numResults,
            "contents": {
                "highlights": True,
                "summary": True,
            }
        }

        # Add optional parameters if provided
        if includeDomains:
            _params["includeDomains"] = includeDomains
        if excludeDomains:
            _params["excludeDomains"] = excludeDomains
        if includeText:
            _params["includeText"] = includeText
        if excludeText:
            _params["excludeText"] = excludeText

        # Endpoint
        _endpoint = "https://api.exa.ai/search"
       
        # Make a request
        async with _session.post(_endpoint, headers=_header, json=_params) as _response:
            # Raise an exception
            try:
                _response.raise_for_status()
                # Hide sensitive data by abstracting it
            except aiohttp.ClientConnectionError:
                raise Exception(f"Failed to fetch web search results with code {_response.status}, reason: {_response.reason}")
    
            _data = await _response.json()

            # Check if the data is empty
            if not _data and not _data.get("results"):
                raise Exception("No results found")

        # Build request
        _output = {
            "guidelines": "You must always provide references and format links with [Page Title](Page URL). As possible, rank the most relevant and fresh sources based on dates.",
            "formatting_rules": "Do not provide links as [Page URL](Page URL), always provide a title as this [Page Title](Page URL), if it doesn't just directly send the URL",
            "formatting_reason": "Now the reason for this is Discord doesn't nicely format the links if you don't provide a title",
            "showLinks": "No need to list all references, only most relevant ones",
            "results": []
        }
        for _results in _data["results"]:
            # Append the data
            _output["results"].append({
                "title": _results.get("title"),
                "url": _results["url"],
                "summary": _results.get("summary"),
                "highlights": _results.get("highlights"),
                "publishedDate": _results.get("publishedDate"),
            })

        if not _output["results"]:
            raise Exception("No results fetched")
        
         # Embed that contains first 10 sources
        _sembed = discord.Embed(
            title="Web Sources"
        )

        # Iterate description
        _desclinks = []
        for _results in _output["results"]:
            if len(_desclinks) <= 10:
                _desclinks.append(f"- [{_results['title'].replace("/", " ")}]({_results['url']})")
            else:
                _desclinks.append("...and more results")
                break
        _sembed.description = "\n".join(_desclinks)
        _sembed.set_footer(text="Used search tool powered by Exa to fetch results")
        await self.method_send(f"🔍 Searched for **{query}**", embed=_sembed)
        
        return _output

        