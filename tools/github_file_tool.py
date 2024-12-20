# Built in Tools
from os import environ
import aiohttp
import base64

# Function implementations
class Tool:
    tool_human_name = "GitHub"
    tool_name = "github_file_tool"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = {
            "name": self.tool_name,
            "description": "Retrieve file content from a GitHub repository or set of files, brainstorm and debug code.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "filepath": {
                        "type": "OBJECT",
                        "properties": {
                            "files": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "STRING"
                                }
                            }
                        },
                        "required": ["files"]
                    },
                    "repo": {
                        "type": "STRING"
                    },
                    "branch": {
                        "type": "STRING"
                    }
                },
                "required": ["filepath", "repo"]
            }
        }
    
    async def _tool_function(self, filepath: dict, repo: str, branch: str = "master"):
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

        # Access the files key
        filepath = filepath["files"]

        # Iterate over the filepath
        for _files in filepath:
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
                    raise ValueError(f"GitHub API returned status code {_response.status}")
                
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





