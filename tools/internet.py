# Built in Tools
from os import environ
import aiohttp
import discord

class Tool:
    tool_human_name = "Internet"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "bing_search",
                "description": "Search and fetch latest information and pull videos with Bing.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING"
                        },
                        "n_results": {
                            "type": "INTEGER",
                        },
                        "show_youtube_videos": {
                            "type": "BOOLEAN"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "google_search",
                "description": "Search and fetch latest information, get detailed and verifiable answers with Google Search. Use Google Search to provide up-to-date and quality verifiable answers.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING"
                        },
                        "n_results": {
                            "type": "INTEGER",
                        },
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "youtube",
                "description": "Summarize and gather insights from a YouTube video.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING"
                        },
                        "n_results": {
                            "type": "INTEGER",
                        },
                    },
                    "required": ["query"]
                }
            }
        ]

    
    async def _tool_function_bing_search(self, query: str, n_results: int = 10, show_youtube_videos: bool = False):
        # Must not be 50
        if n_results > 50:
            n_results = 10

        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized and web browsing cannot continue, please check the bot configuration")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Bing Subscription Key
        if not environ.get("BING_SUBSCRIPTION_KEY"):
            raise ValueError("Bing subscription key not set")
        
        _header = {"Ocp-Apim-Subscription-Key": environ.get("BING_SUBSCRIPTION_KEY")}
        _params = {"q": query, "count": n_results, "safeSearch": "Strict"}
        _endpoint = "https://api.bing.microsoft.com/v7.0/search"

        # Make a request
        async with _session.get(_endpoint, headers=_header, params=_params) as _response:
            _imsg = await self.method_send(f"🔍 Searching for **{query}**")

            # Raise an exception
            try:
                _response.raise_for_status()
                # Hide sensitive data by abstracting it
            except aiohttp.ClientConnectionError:
                raise Exception("Failed to fetch Bing search results with code {_response.status}, reason: {_response.reason}")
    
            _data = (await _response.json())["webPages"]["value"]

            # Check if the data is empty
            if not _data:
                return f"No results found for **{query}**"
            
        # Return the data as dict
        _output = [{
            "guidelines": "You must always provide references and format links with [Page Title](Page URL)",
            "formatting_rules": "Do not provide links as [Page URL](Page URL), always provide a title as this [Page Title](Page URL), if it doesn't just directly send the URL",
            "formatting_reason": "Now the reason for this is Discord doesn't nicely format the links if you don't provide a title",
            "results": []
        }]
        for _results in _data:
            await _imsg.edit(f"🔍 Reading **{_results["name"]}**")

            # Append the data
            _output[0]["results"].append({
                "title": _results["name"],
                "excerpts": _results["snippet"],
                "url": _results["url"]
            })

        # If the user wants to show relevant videos
        if show_youtube_videos:
            _params = {"q": f"{query} site:youtube.com", "count": 4, "safeSearch": "Strict"}
            _endpoint_video = "https://api.bing.microsoft.com/v7.0/videos/search"

            async with _session.get(_endpoint_video, headers=_header, params=_params) as _response:
                await _imsg.edit(f"🔍 Searching for **{query}** videos")

                try:
                    _response.raise_for_status()
                except aiohttp.ClientConnectionError:
                    _output[0]["video_results"] = "No video results found"
                    await _imsg.delete()
                    return _output
                
                _data = (await _response.json())["value"]
                if not _data:
                    _output[0]["video_results"] = "No video results found"
                    await _imsg.delete()
                    return _output
                
                await _imsg.edit("📽️ Let me look some relevant videos for you")
                
                # Add additional guidelines
                _output[0]["video_result_guidelines"] = "Same as the former guidelines but only rank relevant YouTube videos to the user!"
                _output[0]["video_result_rules"] = "You can only choose one YouTube video and put it at the end of your responses so it will be displayed to the user better."
                _output[0]["video_results"] = []
                
                for _results in _data:
                    _output[0]["video_results"].append({
                        "video_title": _results["name"],
                        "video_url": _results["contentUrl"],
                        "video_description": _results["description"]
                    })
        
        # Embed that contains first 10 sources
        _sembed = discord.Embed(
            title="Sources with Bing"
        )

        # Iterate description
        _desclinks = []
        for _results in _output[0]["results"]:
            if len(_desclinks) <= 10:
                _desclinks.append(f"- [{_results['title']}]({_results['url']})")
            else:
                break
        _sembed.description = "\n".join(_desclinks)

        # Add footer about Microsoft Privacy Statement
        _sembed.set_footer(text="Used Bing search tool to fetch results, https://www.microsoft.com/en-us/privacy/privacystatement")
        await self.method_send(embed=_sembed)

        await _imsg.delete()
        return _output
    
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
    
    async def _tool_function_youtube(self, query: str, n_results: int = 10):
        # Must not be above 50
        if n_results > 50:
            n_results = 10

        # Using piped.video to get the video data
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if we have YOUTUBE_DATA_v3_API_KEY is set
        if not environ.get("YOUTUBE_DATA_v3_API_KEY"):
            raise ValueError("YouTube Data v3 API key not set, please go to https://console.cloud.google.com/apis/library/youtube.googleapis.com and get an API key under Credentials in API & Services")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

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

        await self.method_send(f"🔍 Searched for **{query}**")

        return _videos
