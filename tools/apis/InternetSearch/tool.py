from os import environ
import aiohttp
import discord
import logging

# Function implementations
class Tools:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def tool_web_search(self, query: str = None, searchType: str = "auto", numResults: int = 5, includeDomains: list = None, excludeDomains: list = None, includeText: list = None, excludeText: list = None, showHighlights: bool = False, showSummary: bool = False):
        if not query or not query.strip():
            raise ValueError("query parameter is required and cannot be empty")
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for post requests")
            _clientAIOHTTP = self.discord_bot.aiohttp_instance
        else:
            logging.info("Creating new aiohttp client session for post requests")
            _clientAIOHTTP = aiohttp.ClientSession()

        _session: aiohttp.ClientSession = _clientAIOHTTP

        # Bing Subscription Key
        if not environ.get("EXA_AI_KEY"):
            raise ValueError("EXA_AI_KEY key not set")
        
        _header = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": environ.get("EXA_AI_KEY")
        }
        
        # Construct params with proper validation
        _params = {
            "query": query.strip(),
            "type": searchType,
            "numResults": max(1, min(numResults, 10))  # Ensure valid range
        }

        # Add optional parameters if provided and valid
        if includeDomains and isinstance(includeDomains, list):
            _params["includeDomains"] = includeDomains
        if excludeDomains and isinstance(excludeDomains, list):
            _params["excludeDomains"] = excludeDomains
        if includeText and isinstance(includeText, list):
            _params["includeText"] = includeText
        if excludeText and isinstance(excludeText, list):
            _params["excludeText"] = excludeText

        # Add contents if needed
        if showHighlights or showSummary:
            _params["contents"] = {}
            if showHighlights:
                _params["contents"]["highlights"] = True
            if showSummary:
                _params["contents"]["summary"] = True

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
        await self.discord_ctx.channel.send(f"🔍 Searched for **{query}**", embed=_sembed)
        
        return _output

    async def tool_url_browse(self, url: str):
        # Powered by Jina AI
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for GET requests using Jina AI")
            _clientAIOHTTP = self.discord_bot.aiohttp_instance
        else:
            logging.info("Creating new aiohttp client session for GET requests using Jina AI")
            _clientAIOHTTP = aiohttp.ClientSession()

        _session: aiohttp.ClientSession = _clientAIOHTTP
        _endpoint = f"https://r.jina.ai/{url}"

        await self.discord_ctx.channel.send(f"🖱️ Browsing: **`{url}`**")

        async with _session.get(_endpoint) as _response:
            if _response.status != 200:
                raise Exception(f"Failed to fetch URL content with code {_response.status}, reason: {_response.reason}")
            _data = await _response.text()

        # Return the data
        return {
            "url": url,
            "content": _data
        }


    async def tool_youtube_video_search(self, query: str, n_results: int = 10):
        # Must not be above 50
        if n_results > 50:
            n_results = 10

        # Using piped.video to get the video data
        if not hasattr(self.discord_bot, "aiohttp_instance"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if we have YOUTUBE_DATA_v3_API_KEY is set
        if not environ.get("YOUTUBE_DATA_v3_API_KEY"):
            raise ValueError("YouTube Data v3 API key not set, please go to https://console.cloud.google.com/apis/library/youtube.googleapis.com and get an API key under Credentials in API & Services")

        _session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance

        # YouTube Data v3 API Endpoint
        _endpoint = "https://www.googleapis.com/youtube/v3/search"

        # Parameters
        _params = {
            "part": "snippet",
            "maxResults": n_results,
            "q": query,
            "safeSearch": "strict",
            "key": environ.get("YOUTUBE_DATA_v3_API_KEY")
        }

        async with _session.get(_endpoint, params=_params) as _response:
            _data = await _response.json()

            # If the Content-Type is not application/json
            if "application/json" not in _response.headers["Content-Type"]:
                raise Exception("The response from the YouTube API is not in JSON format")
            
            # If the response is not successful
            if _response.status != 200:
                raise Exception(f"Failed to fetch YouTube search results with code {_response.status}, reason: {_response.reason}")
            
        # Iterate over items list
        _videos = [
            {
                "guidelines": "You must format the links with [Video Title](Video URL), always provide video links",
                "rankingByRelevanceGuidelines": "Depending on the user query, rank the videos by relevance based on title, description, and its channel. Including the published date.",
                "contentGuidelines": "Avoid presenting videos that may be potentially disturbing (e.g. extreme creepypasta, scary PSA horrids, signal intrusion, porn, etc.)",
                "rules": "If possible, provide a single relevant video link depending on the user query instead of bulleted multiple links",
                "videos": []
            }
        ]
        for _item in _data["items"]:
            # Check if kind is video
            if _item["id"]["kind"] != "youtube#video":
                continue

            _videos[0]["videos"].append({
                "title": _item["snippet"]["title"],
                "description": _item["snippet"]["description"],
                "url": f"https://www.youtube.com/watch?v={_item['id']['videoId']}",
                "channel": _item["snippet"]["channelTitle"],
                "publishedAt": _item["snippet"]["publishedAt"]
            })

        # If the videos list is empty
        if not _videos[0]["videos"]:
            return f"No videos found for the given query: {query}"

        await self.discord_ctx.channel.send(f"🔍 Searched for **{query}**")

        return _videos