# Built in Tools
from os import environ
import aiohttp
import discord

# Function implementations
class Tool:
    tool_human_name = "Browse with Bing"
    tool_name = "bing_search"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "name": self.tool_name,
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
        }

    
    async def _tool_function(self, query: str, n_results: int = 10, show_youtube_videos: bool = False):
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
                return "Failed to fetch Bing search results with code {_response.status}, reason: {_response.reason}"
    
            _data = (await _response.json())["webPages"]["value"]

            # Check if the data is empty
            if not _data:
                return "No results found"
            
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
