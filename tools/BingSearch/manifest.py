class ToolManifest:
    tool_human_name = "Bing Search"
    bing_search_tool_description = "Search and fetch latest information and pull videos with Bing, perform calculations, or fetch real-time data."
    url_extractor_tool_description = "Extract URLs to summarize"
    def __init__(self):
        self.tool_schema = [ 
            {
                "name": "bing_search",
                "description": self.bing_search_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for, you can use search operators for more sophisticated searches"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "The number of results to fetch, it's recommended to set from 1-3 for simple queries, 4-6 for queries require more corroborating sources, and 7 or more for complex queries"
                        },
                        "show_youtube_videos": {
                            "type": "boolean",
                            "description": "Show relevant YouTube videos"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "url_extractor",
                "description": self.url_extractor_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["urls"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]