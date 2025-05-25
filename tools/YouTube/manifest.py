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
                        },
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
                        }
                    },
                    "required": ["video_id", "corpus"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]