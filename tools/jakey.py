# Built in Tools
from os import environ
from urllib.parse import urlparse
import aiohttp
import discord
import inspect
import io
import aiofiles.os
import asyncio
import importlib
import base64
import html
import re

# Function implementations
class Tool:
    tool_human_name = "Tools"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        # Initialize tool_schema directly with all schemas
        self.tool_schema = [
            # Bing search schemas
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
            },
            # Audio generator schema
            {
                "name": "audio_generator",
                "description": "Generate audio from text using Azure Text-to-Speech",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {
                            "type": "STRING"
                        },
                        "voice": {
                            "type": "STRING",
                            "enum": [
                                "MALE",
                                "FEMALE",
                                "CUTE"
                            ]
                        }
                    },
                    "required": ["text", "voice"]
                }
            },
            # GitHub schemas
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
                            },
                            "description": "The file paths to retrieve from the repository. Must start with /"
                        },
                        "repo": {
                            "type": "STRING",
                            "description": "The repository in the format owner/repo"
                        },
                        "branch": {
                            "type": "STRING",
                            "description": "The branch name, default is master"
                        }
                    },
                    "required": ["files", "repo"]
                }
            },
            {
                "name": "github_search_tool",
                "description": "Search for code, commits, repositories, issues and PRs on GitHub.",
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
                            ],
                            "description": "The type of search to perform"
                        },
                        "query": {
                            "type": "STRING",
                            "description": "The search query to search for, you can use search qualifiers, the character limit is 256"
                        },
                        "page": {
                            "type": "INTEGER",
                            "description": "Pagination, default is 1. You can paginate for more results"
                        }
                    },
                    "required": ["search_type", "query"]
                }
            },
            # Google search schemas
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
            # Ideation tools schemas
            {
                "name": "canvas",
                "description": "Ideate, brainstorm, and create draft content inside Discord thread to continue conversation with specified topic and content",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "thread_title": {
                            "type": "STRING",
                            "description": "The title of the thread"
                        },
                        "plan": {
                            "type": "STRING",
                            "description": "The plan for the topic"
                        },
                        "content": {
                            "type": "STRING",
                            "description": "The elaborate overview of the topic within the thread"
                        },
                        "code": {
                            "type": "STRING",
                            "description": "Optional code snippet for the topic"
                        },
                        "todos": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            },
                            "description": "Optional potential todos"
                        }
                    },
                    "required": ["thread_title", "plan", "content"]
                }
            },
            {
                "name": "artifacts",
                "description": "Create convenient downloadable artifacts when writing code, markdown, text, or any other human readable content. When enabled, responses with code snippets and other things that demands file operations implicit or explictly will be saved as artifacts as Discord attachment.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "file_contents": {
                            "type": "STRING",
                            "description": "The content of the file, it can be a code snippet, markdown content, body of text."
                        },
                        "file_name": {
                            "type": "STRING",
                            "description": "The filename of the file, it's recommended to avoid using binary file extensions like .exe, .zip, .png, etc."
                        }
                    },
                    "required": ["file_contents", "file_name"]
                }
            },
            # Image generator schemas
            {
                "name": "image_generator",
                "description": "Generate or restyle images using natural language or from description using Stable Diffusion 3.5",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_description": {
                            "type": "STRING",
                            "description": "The prompt of the image to generate"
                        }
                    },
                    "required": ["image_description"]
                }
            },
            {
                "name": "image_to_linedrawing",
                "description": "Restyle images to line drawings based from the given image",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The discord attachment URL of the image file"
                        },
                        "mode": {
                            "type": "STRING",
                            "enum": ["Simple Lines", "Complex Lines"],
                            "description": "The style of the line drawing, use your image analysis capabilities to see which suites best for conversion. Use simple lines for images that look simple and animated, complex for detailed images"
                        }
                    },
                    "required": ["discord_attachment_url", "mode"]
                }
            },
            # Voice tools schemas
            {
                "name": "voice_cloner",
                "description": "Clone voices and perform TTS tasks from the given audio files",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The discord attachment URL of the audio file"
                        },
                        "text": {
                            "type": "STRING",
                            "description": "The text for the target voice to dictate the text"
                        }
                    },
                    "required": ["discord_attachment_url", "text"]
                }
            },
            {
                "name": "audio_editor",
                "description": "Edit audio, simply provide the description for editing, and EzAudio will do the rest",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The discord attachment URL of the audio file"
                        },
                        "prompt": {
                            "type": "STRING",
                            "description": "The prompt for the model to add elements to the audio"
                        },
                        "edit_start_in_seconds": {
                            "type": "NUMBER",
                            "description": "The start time in seconds to edit the audio"
                        },
                        "edit_length_in_seconds": {
                            "type": "NUMBER",
                            "description": "The length in seconds to edit the audio"
                        }
                    },
                    "required": ["discord_attachment_url", "prompt"]
                }
            },
            # YouTube schema
            {
                "name": "youtube",
                "description": "Summarize and gather insights from a YouTube video.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The query to search for"
                        },
                        "n_results": {
                            "type": "INTEGER",
                            "description": "The number of results to fetch"
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
            # Raise an exception
            try:
                _response.raise_for_status()
                # Hide sensitive data by abstracting it
            except aiohttp.ClientConnectionError:
                raise Exception(f"Failed to fetch Bing search results with code {_response.status}, reason: {_response.reason}")

            _data = (await _response.json())["webPages"]["value"]

            # Check if the data is empty
            if not _data:
                return f"No results found for **{query}**"

        # Return the data as dict
        _output = [{
            "guidelines": "You must always provide references and format links with [Page Title](Page URL). As possible, rank the most relevant and fresh sources based on dates.",
            "formatting_rules": "Do not provide links as [Page URL](Page URL), always provide a title as this [Page Title](Page URL), if it doesn't just directly send the URL",
            "formatting_reason": "Now the reason for this is Discord doesn't nicely format the links if you don't provide a title",
            "results": []
        }]
        for _results in _data:
            # Append the data
            _output[0]["results"].append({
                "title": _results["name"],
                "excerpts": _results["snippet"],
                "url": _results["url"],
                "dateLastCrawled": _results.get("dateLastCrawled") or "Date last crawled data not available",
                "datePublished": _results.get("datePublished") or "Date published data not available"
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
                _desclinks.append("...and more results")
                break
        _sembed.description = "\n".join(_desclinks)

        # Add footer about Microsoft Privacy Statement
        _sembed.set_footer(text="Used Bing search tool to fetch results, https://www.microsoft.com/en-us/privacy/privacystatement")
        await self.method_send(f"🔍 Searched for **{query}**", embed=_sembed)
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

    # Audio generator using Azure Text-to-Speech
    async def _tool_function_audio_generator(self, text: str, voice: str):
        # Check if AZURE_TTS_KEY is set
        if not environ.get("AZURE_TTS_KEY"):
            raise ValueError("Azure TTS API key is not set, please set it in the environment variables")

        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")

        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Check if AZURE_TTS_REGION is set if not, assume its eastus
        if not environ.get("AZURE_TTS_REGION"):
            environ["AZURE_TTS_REGION"] = "eastus"

        _headers = {
            "Ocp-Apim-Subscription-Key": environ.get("AZURE_TTS_KEY"),
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-160kbitrate-mono-mp3"
        }

        # Check for voices
        # MALE = en-US-DerekMultilingualNeural
        # FEMAILE = en-US-JennyNeural
        # CUTE = en-US-AnaNeural
        if voice == "MALE":
            _voiceType = "en-US-DerekMultilingualNeural"
            _voiceGender = "Male"
        elif voice == "FEMALE":
            _voiceType = "en-US-JennyNeural"
            _voiceGender = "Female"
        elif voice == "CUTE":
            _voiceType = "en-US-AnaNeural"
            _voiceGender = "Female"

        _xmlData = inspect.cleandoc(rf"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                <voice xml:gender='{_voiceGender}' name='{_voiceType}'>
                    {text}
                </voice>
            </speak>""")

        # Make a request
        async with _client_session.post(f"https://{environ["AZURE_TTS_REGION"]}.tts.speech.microsoft.com/cognitiveservices/v1", data=_xmlData, headers=_headers) as _response:
            if _response.status != 200:
                raise Exception(f"Failed to generate audio with code {_response.status}, reason: {_response.reason}")

            # Ensure the output is audio and in binary format
            if not "audio" in _response.headers["Content-Type"]:
                raise Exception("The response from the Azure TTS API is not in audio format")

            # Send the audio
            _audio = await _response.content.read()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_audio), filename="voice.mp3"))

        # Cleanup
        return "Audio success and the file should be sent automatically"

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

            # Get the webpage date IF "date" in pagemap/metatags is present
            _date = "No date from metatags extracted"
            if "pagemap" in _item and "metatags" in _item["pagemap"]:
                if "date" in _item["pagemap"]["metatags"][0]:
                    _date = _item["pagemap"]["metatags"][0]["date"]

            _output[0]["results"].append({
                "title": _item["title"],
                "link": _item["link"],
                "excerpt": _item["snippet"],
                "date": _date
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

    async def _tool_function_canvas(self, thread_title: str, plan: str, content: str, code: str = None, todos: list = None):
        # Check if we're in a server
        if not self.discord_ctx.guild:
            raise Exception("This tool can only be used in a server")

        # Create a new thread
        _msgstarter = await self.discord_ctx.channel.send(f"📃 Planning **{thread_title}**")
        _thread = await _msgstarter.create_thread(name=thread_title, auto_archive_duration=1440)

        # Send the plan
        # Encode and decode using bytes and later decode it again using string escape
        await _thread.send(f"**Plan:**\n{plan}")
        # Send the content
        await _thread.send(f"**Content:**\n{content}")
        # Send the code if available
        if code:
            await _thread.send(f"**Code:**\n```{code}```")
        # Send the todos if available
        if todos:
            await _thread.send(f"**Todos:**\n")
            for _todo in todos:
                await _thread.send(f"- {_todo}")

        return "Thread created successfully"

    async def _tool_function_artifacts(self, file_contents: str, file_name: str):
        # Send the file
        await self.method_send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"

    # Image generator
    async def _tool_function_image_generator(self, image_description: str):
        # Check if HF_TOKEN is set
        if not environ.get("HF_TOKEN"):
            raise ValueError("HuggingFace API token is not set, please set it in the environment variables")

        # Create image
        message_curent = await self.method_send(f"⌛ Generating **{image_description}**... this may take few minutes")

        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")

        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Payload
        _payload = {
            "inputs": image_description,
        }

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {environ.get('HF_TOKEN')}"
        }

        # Make a request
        async with _client_session.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo", json=_payload, headers=_headers) as _response:
            # Check if the response is not 200 which may print JSON
            # Response 200 would return the binary image
            if _response.status != 200:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")

            # Send the image
            _imagedata = await _response.content.read()

        # Delete status
        await message_curent.delete()

        # Send the image
        await self.method_send(file=discord.File(fp=io.BytesIO(_imagedata), filename="generated_image.png"))

        # Cleanup
        return "Image generation success and the file should be sent automatically"

    async def _tool_function_image_to_linedrawing(self, discord_attachment_url: str, mode: str):
        # Import
        gradio_client = importlib.import_module("gradio_client")

        result = await asyncio.to_thread(
            gradio_client.Client("awacke1/Image-to-Line-Drawings").predict,
            input_img=gradio_client.handle_file(discord_attachment_url),
            ver=mode,
            api_name="/predict"
        )

        # Send the image
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Image restyling success and the file should be sent automatically"

    async def _tool_function_voice_cloner(self, discord_attachment_url: str, text: str):
        # Import
        gradio_client = importlib.import_module("gradio_client")

        message_curent = await self.method_send("🗣️ Ok... please wait while I'm cloning the voice")
        result = await asyncio.to_thread(
            gradio_client.Client("tonyassi/voice-clone").predict,
            text=text,
            audio=gradio_client.file(discord_attachment_url),
            api_name="/predict"
        )

        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Audio editing success"

    async def _tool_function_audio_editor(self, discord_attachment_url: str, prompt: str, edit_start_in_seconds: int = 3, edit_length_in_seconds: int = 5):
        # Validate parameters
        if edit_length_in_seconds > 10 or edit_length_in_seconds < 0.5:
            edit_length_in_seconds = 5

        # Import
        gradio_client = importlib.import_module("gradio_client")

        message_curent = await self.method_send("🎤✨ Adding some magic to the audio...")
        result = await asyncio.to_thread(
            gradio_client.Client("OpenSound/EzAudio").predict,
            text=prompt,
            boundary=2,
            gt_file=gradio_client.handle_file(discord_attachment_url),
            mask_start=edit_start_in_seconds,
            mask_length=edit_length_in_seconds,
            guidance_scale=5,
            guidance_rescale=0,
            ddim_steps=50,
            eta=1,
            random_seed=0,
            randomize_seed=True,
            api_name="/editing_audio_1"
        )

        # Delete status
        await message_curent.delete()

        # Send the audio
        await self.method_send(file=discord.File(fp=result))

        # Cleanup
        await aiofiles.os.remove(result)
        return "Audio editing success"

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