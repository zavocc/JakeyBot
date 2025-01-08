# Built in Tools
from os import environ
import aiohttp
import discord

# Function implementations
class Tool:
    tool_human_name = "Browse with Bing"
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
                            "type": "STRING",
                            "description": "The query to search for, you can use search operators for more sophisticated searches"
                        },
                        "n_results": {
                            "type": "INTEGER",
                            "description": "The number of results to fetch, it's recommended to set from 1-3 for simple queries, 4-6 for queries require more corroborating sources, and 7-10 for complex queries"
                        },
                        "show_youtube_videos": {
                            "type": "BOOLEAN",
                            "description": "Show relevant YouTube videos"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "bing_image_search",
                "description": "Search for similar images using Bing's reverse visual image search capability",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The Discord attachment URL of the image to be sent on Bing's visual search"
                        },
                        "n_results": {
                            "type": "INTEGER",
                            "description": "The number of similar image results to fetch (1-10)"
                        }
                    },
                    "required": ["discord_attachment_url"]
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
                try:
                    _response.raise_for_status()
                except aiohttp.ClientConnectionError:
                    _output[0]["video_results"] = "No video results found"
                    return _output
                
                _data = (await _response.json())["value"]
                if not _data:
                    _output[0]["video_results"] = "No video results found"
                    return _output
                        
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
        return _output
    
    async def _tool_function_bing_image_search(self, discord_attachment_url: str, n_results: int = 5):
        # Validate number of results
        if n_results > 10:
            n_results = 5

        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized and image search cannot continue")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Bing Subscription Key check
        if not environ.get("BING_SUBSCRIPTION_KEY"):
            raise ValueError("Bing subscription key not set")
        
        # Perform pre-request by downloading the CDN of the image and store it{'image' : ('myfile', open(imagePath, 'rb'))}
        # We use aiofiles and aiohttp to download the image
        # We also need to make sure if its less than 1MB
        async with _session.get(discord_attachment_url) as _response:
            if _response.content_length > 1048576:
                raise ValueError("Image size must be less than 1MB")
            
            # Check if the response is successful and is an image
            if _response.status != 200 or not _response.headers["Content-Type"].startswith("image"):
                raise ValueError("Invalid image URL provided")
            
            # Store it on memory
            _image_data = await _response.read()

        _header = {"Ocp-Apim-Subscription-Key": environ.get("BING_SUBSCRIPTION_KEY")}
        _endpoint = "https://api.bing.microsoft.com/v7.0/images/visualsearch"

        # Create form data
        _formdata = aiohttp.FormData()
        _formdata.add_field("image", _image_data, filename="image.jpg")

        # Make the request
        async with _session.post(_endpoint, headers=_header, data=_formdata) as _response:
            try:
                _response.raise_for_status()
            except aiohttp.ClientConnectionError:
                raise Exception(f"Failed to perform reverse image search with code {_response.status}, reason: {_response.reason}")

            _data = await _response.json()
            
            # Check if we have results
            if "tags" not in _data:
                return "No similar images found"

        # Process the results
        _output = [{
            "guidelines": "You must gather insights of Image search result based on the majority of the results",
            "formatting_rules": "Format links as [Title](Webpage URL)",
            "results": []
        }]

        # Ground the response based on the results returned from the image search
        for tag in _data["tags"]:
            if "actions" in tag:
                for action in tag["actions"]:
                    if action.get("actionType") == "VisualSearch":
                        for item in action.get("data", {}).get("value", []):
                            _output[0]["results"].append({
                                "title": item.get("name", "Untitled Image"),
                                "host_page_url": item.get("hostPageUrl"),
                                "thumbnail_url": item.get("thumbnailUrl")
                            })

                            
        
        # Create and send embed with results
        _sembed = discord.Embed(
            title="Similar Images Found"
        )

        # Add results to embed
        _desclinks = []
        for result in _output[0]["results"][:10]:  # Limit to first 10 results
            _desclinks.append(f"- [{result['title']}]({result['host_page_url']})")
        
        _sembed.description = "\n".join(_desclinks)
        _sembed.set_footer(text="Powered by Bing Visual Search API")
        
        # Add the original image as thumbnail
        _sembed.set_thumbnail(url=discord_attachment_url)
        
        await self.method_send(embed=_sembed)
        return _output

    # URL Extractor
    async def _tool_function_url_extractor(self, urls: list):
        # Must be 5 or below else error out
        if len(urls) > 5:
            raise ValueError("URLs must be 10 or below")
        
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

                # Check if its a binary file which must error out
                if "application/octet-stream" in _response.headers["Content-Type"] and "Content-Disposition" in _response.headers:
                    _output.append({
                        "url": _url,
                        "content": "Binary file, cannot extract text"
                    })

                _data = await _response.text()
                _output.append({
                    "url": _url,
                    "content": _data
                })

        # Delete the message
        if _imsg:
            await _imsg.delete()

        return _output
