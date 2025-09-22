from os import environ
import aiohttp
import base64
import discord
import html
import re

# Function implementations
class Tools:
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    async def tool_web_search(self, query: str = None, searchType: str = "auto", numResults: int = 5, includeDomains: list = None, excludeDomains: list = None, includeText: list = None, excludeText: list = None, showHighlights: bool = False, showSummary: bool = False):
        if not query or not query.strip():
            raise ValueError("query parameter is required and cannot be empty")
        
        if not hasattr(self.discord_bot, "aiohttp_instance"):
            raise Exception("aiohttp client session for get requests not initialized and web browsing cannot continue, please check the bot configuration")

        _session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance

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
        await self.method_send(f"🔍 Searched for **{query}**", embed=_sembed)
        
        return _output


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

        await self.method_send(f"🔍 Searched for **{query}**")

        return _videos


    # GitHub
    # A method to extract relevant result from GitHub API to only extract the necessary information
    # https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#about-search
    async def _search_extractor(self, search_type: str, search_result: dict):
        _search_results = [
            {
                "total_count": search_result["total_count"],
                "incomplete_results": search_result["incomplete_results"],
                "guidelines": "As a GitHub Search Agent, you must format the search results [with hyperlinks](to://format/nicely/the/links)",
                "ranking_guidelines": "Rank the search results based on the score provided by the GitHub API"
            }
        ]

        if search_type == "CODE":
            for _result in search_result["items"]:
                _search_results.append({
                    "name": _result["name"],
                    "path": _result["path"],
                    "url": _result["html_url"],
                    "repository": _result["repository"]["full_name"],
                    "score": _result["score"]
                })
        elif search_type == "COMMITS":
            for _result in search_result["items"]:
                _search_results.append({
                    "commit": _result["commit"]["message"],
                    "commit_author": _result["commit"]["author"],
                    "commiter": _result["commit"]["committer"],
                    "message": _result["commit"]["message"],
                    "repository": _result["repository"]["full_name"],
                    "url": _result["html_url"],
                    "score": _result["score"]
                })
        elif search_type == "REPOSITORIES":
            for _result in search_result["items"]:
                _search_results.append({
                    "name": _result["name"],
                    "url": _result["html_url"],
                    "description": _result["description"],
                    "is_fork": _result["fork"],
                    "score": _result["score"]
                })
        elif search_type == "ISSUE" or search_type == "PR":
            for _result in search_result["items"]:
                _search_results.append({
                    "title": _result["title"],
                    "body": _result["body"],
                    "url": _result["html_url"],
                    "state": _result["state"],
                    "locked": _result["locked"],
                    "score": _result["score"]
                })
        
        return _search_results

    async def tool_github_file_tool(self, files: list, repo: str, branch: str = "master"):
        # Must initialize the aiohttp client session
        if not hasattr(self.discord_bot, "aiohttp_instance"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if we have GITHUB_TOKEN is set
        if not environ.get("GITHUB_TOKEN"):
            raise ValueError("GitHub API token not set, please go to https://github.com/settings/tokens?type=beta")

        _session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance

        # Headers
        _headers = {
            "Authorization": f"Bearer {environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+raw",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        _codebasemetadatas = []

        # Iterate over the filepath
        for _files in files:
            # Send
            await self.method_send(f"📎 Reading the file **{_files}**")

            # Check if the filepath starts with /
            if not _files.startswith("/"):
                _files = f"/{_files}"

            # GitHub API endpoint
            _endpoint = f"https://api.github.com/repos/{repo}/contents" + _files

            async with _session.get(_endpoint, headers=_headers, params={"ref": branch}) as _response:
                # Check if the response is successful
                if _response.status != 200:
                    raise Exception(f"GitHub API returned status code {_response.status}")
                
                # Parse the response
                _response_json = await _response.json()

                # Check if the file is binary by decoding the base64 content
                try:
                    _decoded_content = base64.b64decode(_response_json["content"]).decode("utf-8")
                except UnicodeDecodeError:
                    _decoded_content = "Binary file, unable to decode content"

                # Append the codebase metadata
                _codebasemetadatas.append({
                    "filename": _response_json["name"],
                    "real_url": _response_json["_links"]["html"],
                    "content": _decoded_content
                })

        # Check if codebase metadata is empty
        if not _codebasemetadatas:
            raise ValueError("No files found in the specified paths")
        
        return _codebasemetadatas
    
    async def tool_github_search_tool(self, search_type: str, query: str, page: int = 1):
        # Check if search query is
        # - Less than 256 characters
        # - Must not be crooked (e.g. literal code block)
        # - Must not contain newlines
        # - Must be treated as a single line
        if len(query) > 256:
            raise ValueError("Search query must be less than 256 characters")

        # Ensure the search query is a single line, must not contain newlines or code blocks
        if "\n" in query:
            raise ValueError("Must be a proper search query, must not contain newlines or code blocks")
        
        # Must initialize the aiohttp client session
        if not hasattr(self.discord_bot, "aiohttp_instance"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Must not include symbols like --, .., etc. since this will cause 422 error
        # Except for the search qualifiers such as is:issue, is:pull-request
        # And except for quotes, pls visit regex101.com for reference
        _invalid_patterns = [
            r'--',           # Double dash
            r'\.\.',         # Double dot
            r'\\\\',        # Double backslash
            r'[<>|{}[\]^~`]' # Invalid special characters
        ]
        # We just need to remove these invalid patterns
        for _pattern in _invalid_patterns:
            query = re.sub(_pattern, " ", query)

        # Strip the query
        query = query.strip()

        _session: aiohttp.ClientSession = self.discord_bot.aiohttp_instance

        # Check if we have GITHUB_TOKEN is set
        if not environ.get("GITHUB_TOKEN"):
            raise ValueError("GitHub API token not set, please go to https://github.com/settings/tokens?type=beta")

        # Headers
        _headers = {
            "Authorization": f"Bearer {environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+raw",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Search endpoint
        _search_qualifier = None
        if search_type == "CODE":
            _search_endpoint = "https://api.github.com/search/code"
        elif search_type == "COMMITS":
            _search_endpoint = "https://api.github.com/search/commits"
        elif search_type == "REPOSITORIES":
            _search_endpoint = "https://api.github.com/search/repositories"
        elif search_type == "ISSUE":
            if "is:issue" not in query:
                _search_qualifier = "is:issue"
            _search_endpoint = "https://api.github.com/search/issues"
        elif search_type == "PR":
            if "is:pull-request" not in query:
                _search_qualifier = "is:pull-request"
            _search_endpoint = "https://api.github.com/search/issues"

        if _search_qualifier:
            query = f"{query} {_search_qualifier}"

        _searchResult = None

        # Search
        await self.method_send(f"🔍 Using GitHub API to search for **{query}**")

        # We cap the search results to 7 so that LLM doesn't get overwhelmed
        async with _session.get(_search_endpoint, headers=_headers, params={"q": html.escape(query), "page": page, "per_page": 7}) as _response:
            # Check if the response is successful
            if _response.status != 200:
                raise Exception(f"GitHub API returned status code {_response.status}")
            
            # Parse the response
            _searchResult = await _response.json()

            # Extract the search results
            _searchResult = await self._search_extractor(search_type, _searchResult)

        # Check if the search result is empty
        if not _searchResult:
            raise ValueError("No results found for the specified query")
        
        return _searchResult
