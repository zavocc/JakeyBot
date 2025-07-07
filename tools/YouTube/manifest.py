class ToolManifest:
    tool_human_name = "YouTube"
    youtube_search_description = "Summarize and gather insights from a YouTube video."
    youtube_corpus_description = "Call YouTube subagent and get summaries and gather insights from a YouTube video."
    def __init__(self):
        self.tool_schema = [
            {
                "name": "youtube_search",
                "description": self.youtube_search_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "The number of results to fetch"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "youtube_corpus",
                "description": self.youtube_corpus_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID from the URL or relevant context provided"
                        },
                        "corpus": {
                            "type": "string",
                            "description": "Natural language description about the video to gather insights from and get excerpts"
                        },
                        "fps_mode": {
                            "type": "string",
                            "description": "The number of frames per second to process the video. Default is dense - 1. Options: dense - 1, fast - 5, sparse - 7. It's recommended to choose the best preferences based on video context clues from search results. Avoid using dense for static videos like lectures.",
                            "enum": [
                                "dense",
                                "fast",
                                "sparse"
                            ]
                        },
                        "start_time": {
                            "type": "integer",
                            "description": "Start time in seconds"
                        },
                        "end_time": {
                            "type": "integer",
                            "description": "End time in seconds"
                        },
                        "media_resolution": {
                            "type": "string",
                            "description": "Default media resolution for the video: default (unspecified), medium, or low. Default or medium would mean the vision can better understand image fidelity but at cost of latency and context limitations. Low can compromise quality but it allows faster and can accept upto 3 hours of video. Medium or default can accept upto 1 hour of video.",
                            "enum": [
                                "MEDIA_RESOLUTION_UNSPECIFIED",
                                "MEDIA_RESOLUTION_MEDIUM",
                                "MEDIA_RESOLUTION_LOW"
                            ]
                        }
                    },
                    "required": ["video_id", "corpus"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]