from google.genai import types
from os import environ
import aiohttp
import google.genai as genai
import json

class Tool:
    tool_human_name = "YouTube"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "youtube_search",
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
            },
            {
                "name": "youtube_corpus",
                "description": "Call YouTube subagent and get summaries and gather insights from a YouTube video.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "video_id": {
                            "type": "STRING",
                            "description": "The YouTube video ID from the URL or relevant context provided"
                        },
                        "corpus": {
                            "type": "STRING",
                            "description": "Natural language description about the video to gather insights from and get excerpts"
                        }
                    },
                    "required": ["video_id", "corpus"]
                }
            }
        ]
    
    async def _tool_function_youtube_search(self, query: str, n_results: int = 10):
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
    
    async def _tool_function_youtube_corpus(self, video_id: str, corpus: str):
        # Check if global aiohttp and google genai client session is initialized
        if not hasattr(self.discord_bot, "_gemini_api_client"):
            raise Exception("gemini api client isn't set up, please check the bot configuration")
        
        _api_client: genai.Client = self.discord_bot._gemini_api_client
        
        # JSON schema
        _output_schema = types.Schema(
            type = types.Type.OBJECT,
            required = ["corpus"],
            properties = {
                "corpus": types.Schema(
                    type = types.Type.ARRAY,
                    items = types.Schema(
                        type = types.Type.OBJECT,
                        required = ["passage", "timestamp"],
                        properties = {
                            "passage": types.Schema(
                                type = types.Type.STRING,
                            ),
                            "timestamp": types.Schema(
                                type = types.Type.STRING,
                            ),
                        },
                    ),
                ),
            },
        )
        _output_result = None

        # Craft prompt
        _crafted_prompt = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=f"https://youtu.be/{video_id}",
                        mime_type="video/*",
                    ),
                    types.Part.from_text(text=f"Get me relevant passage, excerpt, or insights based on the prompt: {corpus}")
                ],
            ),
        ]

        # Generate response
        _response = await _api_client.aio.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=_crafted_prompt,
            config={
                "candidate_count": 1,
                "temperature": 0,
                "max_output_tokens": 8192,
                "response_schema": _output_schema,
                "response_mime_type": "application/json",
                "system_instruction": "Your name is YouTube summarizer, you will need to output relevant passages based on query\nYou must keep the outputs relevant and optimize by only outputting the required passages and timestamps\nThe passage can either be a relevant excerpt or your own summary of the particular scene, do not make repetitive summary."
            }
        )

        # Parse the response
        _output_result = json.loads(_response.text)

        if not _output_result:
            return "No relevant passages found"
        else:
            return _output_result
