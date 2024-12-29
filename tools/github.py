# Built in Tools
from os import environ
import aiohttp
import base64
import html
import re

# Function implementations
class Tool:
    tool_human_name = "GitHub"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "github_file_tool",
                "description": "Retrieve file content from a GitHub repository or set of files, brainstorm and debug code.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "files": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            }
                        },
                        "repo": {
                            "type": "STRING"
                        },
                        "branch": {
                            "type": "STRING"
                        }
                    },
                    "required": ["files", "repo"]
                }
            },
            {
                "name": "github_search_tool",
                "description": "Search for code, commits, repositories, issues and PRs on GitHub. Optimize search queries for 256 characters or less, use GitHub search qualifiers to narrow down the search.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "search_type": {
                                "type": "STRING",
                                "enum": [
                                    "CODE",
                                    "COMMITS",
                                    "REPOSITORIES",
                                    "ISSUE",
                                    "PR"
                                ]
                        },
                        "query": {
                            "type": "STRING"
                        },
                        "page": {
                            "type": "INTEGER"
                        }
                    },
                    "required": ["search_type", "query"]
                }
            }
        ]
    
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

    async def _tool_function_github_file_tool(self, files: list, repo: str, branch: str = "master"):
        # Must initialize the aiohttp client session
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        # Check if we have GITHUB_TOKEN is set
        if not environ.get("GITHUB_TOKEN"):
            raise ValueError("GitHub API token not set, please go to https://github.com/settings/tokens?type=beta")

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Headers
        _headers = {
            "Authorization": f"Bearer {environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+raw",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        _codebasemetadatas = []

        # Interstitial
        _interstitial = await self.method_send("🔍 Searching for files in the specified paths")

        # Iterate over the filepath
        for _files in files:
            # Send
            await _interstitial.edit(f"📎 Reading the file **{_files}**")

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
        
        # Delete the interstitial
        if _interstitial:
            await _interstitial.delete()
        
        return _codebasemetadatas
    
    async def _tool_function_github_search_tool(self, search_type: str, query: str, page: int = 1):
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
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
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

        _session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

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