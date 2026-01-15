from os import environ
import aiohttp
import discord
import io
import logging

# Function implementations
class Tools:
    def __init__(self, discord_message, discord_bot):
        self.discord_message = discord_message
        self.discord_bot = discord_bot

    async def tool_web_search(self, query: str = None, searchType: str = "auto", numResults: int = 5, includeDomains: list = None, excludeDomains: list = None, includeText: list = None, excludeText: list = None, showSummary: bool = False, showSourcesList: bool = False):
        if not query or not query.strip():
            raise ValueError("query parameter is required and cannot be empty")
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for post requests")
            _session = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

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
        _params["contents"] = {}
        if showSummary:
            _params["contents"]["summary"] = True

        # Show highlights
        _params["contents"]["highlights"] = True

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
        if showSourcesList:
            _sembed = discord.Embed(
                title="Web Sources"
            )

            # Iterate description
            _desclinks = []
            for _results in _output["results"]:
                if len(_desclinks) <= 10:
                    _desclinks.append(f"- [{_results.get('title', 'No Title').replace("/", " ")}]({_results['url']})")
                else:
                    _desclinks.append("...and more results")
                    break
            _sembed.description = "\n".join(_desclinks)
            _sembed.set_footer(text="Used search tool powered by Exa to fetch results")
        else:
            _sembed = None
        await self.discord_message.channel.send(f"🔍 Searched for **{query}**", embed=_sembed)
        
        return _output

    async def tool_url_browse(self, url: str):
        # Powered by Jina AI
        
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for GET requests using Jina AI")
            _session = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        _endpoint = f"https://r.jina.ai/{url}"

        await self.discord_message.channel.send(f"🖱️ Browsing: **`{url}`**")

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
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for GET requests of YouTube Data v3")
            _session = self.discord_bot.aiohttp_instance
        else:
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

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

        await self.discord_message.channel.send(f"🔍 Searched for **{query}**")

        return _videos


    # List runtimes for code execution
    async def tool_code_execution_list_runtimes(self, language: str):
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for GET requests of Piston")
            _session = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        # Endpoint
        _endpoint = "https://emkc.org/api/v2/piston/runtimes"

        # Make a request
        async with _session.get(_endpoint) as _response:
            if _response.status != 200:
                raise Exception(f"Failed to fetch runtimes with code {_response.status}, reason: {_response.reason}")
            _data = await _response.json()

            # Check if the data is empty
            if not _data:
                raise Exception("No runtimes found")

        # Filter runtimes based on language parameter
        _runtime_info = None
        for _runtime in _data:
            if _runtime.get("language", "").lower() == language.lower():
                _runtime_info = _runtime
                break

        # Return the filtered data
        return _runtime_info

    # Code execution tool
    async def tool_code_execution(self, language: str, version: str, files: list, stdin: str = None, args: list = None):
        # Powered by Piston (https://piston.rs/)
        if hasattr(self.discord_bot, "aiohttp_instance"):
            logging.info("Using existing aiohttp client session for POST requests of Piston")
            _session = self.discord_bot.aiohttp_instance
        else:
            # Throw exception since we don't have a session
            logging.warning("No aiohttp_instance found in discord bot subclass, aborting")
            raise Exception("HTTP Client has not been initialized properly, please try again later.")

        # Validate files format
        if not isinstance(files, list) or not files:
            raise ValueError("files must be a non-empty list")
        
        for file in files:
            if not isinstance(file, dict) or 'name' not in file or 'content' not in file:
                raise ValueError("Each file must be a dict with 'name' and 'content' keys")

        # Construct parameters
        _paramsBuilder = {
            "language": language,
            "version": version,
            "files": files
        }

        # if stdin is provided
        if stdin:
            _paramsBuilder["stdin"] = stdin
        
        # if args is provided
        if args:
            _paramsBuilder["args"] = args

        # Log the request for debugging
        logging.info(f"Piston request: {_paramsBuilder}")

        # Endpoint
        _endpoint = "https://emkc.org/api/v2/piston/execute"

        # Send the code and file
        await self.discord_message.channel.send(f"▶️ Executing code, using version: **{version}** in language: **{language}**")
        for _file in files:
            # Use BytesIO directly (no thread offload needed)
            _buffer = io.BytesIO(_file["content"].encode("utf-8"))
            await self.discord_message.channel.send(
                file=discord.File(fp=_buffer, filename=_file["name"])
            )

        # Make a request
        async with _session.post(_endpoint, json=_paramsBuilder) as _response:
            # Get response text for better error details
            _textResult = await _response.text()

            # Raise an exception with detailed error info
            if _response.status >= 400:
                logging.error(f"Piston error {_response.status}: {_textResult}")
                raise Exception(f"Failed to execute code with status {_response.status}: {_textResult}")

            try:
                _data = await _response.json()

                # Send the output, truncate upto 1500 characters
                if _data.get("run", {}).get("output"):
                    _output = _data["run"]["output"]
                    if len(_output) > 1450:
                        _output = _output[:1450] + "\n...[truncated]"
                    await self.discord_message.channel.send(f"✅ **Code Output:**\n```{_output}\n```")
            except ValueError:
                logging.error(f"Invalid JSON response: {_textResult}")
                raise Exception(f"Invalid response from code execution engine: {_textResult}")

            # Check if the data is empty
            if not _data:
                raise Exception("No response from code execution engine")
         
        # Add guidelines to _data
        _data["guidelines"] = "When providing code execution results, always provide summaries of the code output as first 1300 characters of code is shown in Discord UI. The source code is already sent to Discord chat UI as a file no need to repeat it again in the output."

        return _data
