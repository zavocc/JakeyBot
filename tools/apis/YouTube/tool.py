from .manifest import ToolManifest
from aimodels.gemini import Completions
from core.services.helperfunctions import HelperFunctions
from google.genai import types
from os import environ
import aiohttp
import inspect
import json

class Tool(ToolManifest):
    def __init__(self, method_send, discord_ctx, discord_bot):
        super().__init__()
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot
    
    async def _tool_function_youtube_search(self, query: str, n_results: int = 10):
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
    
    async def _tool_function_youtube_corpus(self, video_id: str, corpus: str, fps_mode: str = "dense", start_time: int = None, end_time: int = None, media_resolution: str = "MEDIA_RESOLUTION_UNSPECIFIED"):
        # Check if global aiohttp and google genai client session is initialized
        if not hasattr(self.discord_bot, "_gemini_api_client"):
            raise Exception("gemini api client isn't set up, please check the bot configuration")
    
        # SYSTEM PROMPT
        _system_prompt = inspect.cleandoc("""Your name is YouTube Q&A, you will need to output relevant passages based on query
        You can either answer questions or provide passages or transcribe the video
        When answering questions you can provide the answer in a single passage element with relevant timestamp""")

        # FPS
        if fps_mode == "dense":
            _fps = 1
        elif fps_mode == "fast":
            _fps = 5
        elif fps_mode == "sparse":
            _fps = 7

        # Craft prompt
        _crafted_prompt = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        file_data=types.FileData(file_uri=f"https://youtube.com/watch?v={video_id}"),
                        video_metadata=types.VideoMetadata(
                            fps=_fps,
                            start_offset=f"{start_time}s" if start_time else None,
                            end_offset=f"{end_time}s" if end_time else None
                        )
                    ),
                    types.Part.from_text(text=f"Get me relevant passage, excerpt, insights or answer questions,  based on the prompt: {corpus}")
                ],
            ),
        ]

        # Provide the base model
        _default_model = HelperFunctions.fetch_default_model(
            model_type="base",
            output_modalities="text",
            provider="gemini"
        )["model_name"]

        # Initiate completions
        _completions = Completions(
            model_name=_default_model,
            discord_ctx=self.discord_ctx,
            discord_bot=self.discord_bot,
        )

        # JSON schema
        _completions._genai_params.update({
            "response_schema": types.Schema(
                type = types.Type.OBJECT,
                required = ["answer"],
                properties = {
                    "answer": types.Schema(
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
            ),
            "response_mime_type": "application/json"
        })
        _output_result = None

        # Set default resolution mode
        _completions._genai_params.update({
            "media_resolution": media_resolution
        })

        # Generate response
        _response = await _completions.completion(
            prompt=_crafted_prompt,
            system_instruction=_system_prompt,
            return_text=False
        )
        # Parse the response
        _output_result = json.loads(_response.text)

        if not _output_result:
            return "No relevant passages found"
        else:
            return _output_result
