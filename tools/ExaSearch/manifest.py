class ToolManifest:
    tool_human_name = "Web Search"
    web_search_tool_description = "Search the web to inform response, use semantic or keyword based search."
    def __init__(self):
        self.tool_schema = [ 
            {
                "name": "web_search",
                "description": self.web_search_tool_description,
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The query to search for"
                        },
                        "searchType": {
                            "type": "STRING",
                            "enum": [
                                "neural",
                                "keyword"
                            ],
                            "description": "The type of search to perform, use keyword to include keywords in the search query, neural for specific searches. If not set, the service will automatically determine the type of search to perform"
                        },
                        "numResults": {
                            "type": "INTEGER",
                            "description": "The number of results to fetch, it's recommended to set from 1-3 for simple queries, 4-6 for queries require more corroborating sources, and 7 or more for complex queries"
                        },
                        "includeDomains": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            },
                            "description": "A list of domains to include in the search results"
                        },
                        "excludeDomains": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            },
                            "description": "A list of domains to exclude from the search results"
                        },
                        "includeText": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            },
                            "description": "A list of text to include in the search results"
                        },
                        "excludeText": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            },
                            "description": "A list of text to exclude from the search results"
                        },
                        "showHighlights": {
                            "type": "BOOLEAN",
                            "description": "Show highlights in the search results, it's recommended to set this true. Disable this if the user explicitly asks to only fetch the results without any summary or highlights to also save costs and time"
                        },
                        "showSummary": {
                            "type": "BOOLEAN",
                            "description": "Show summary in the search results. Disable this if the user explicitly asks to only fetch the results without any summary or highlights to also save costs and time"
                        },
                    },
                    "required": ["query"]
                }
            }
        ]

        # Updated OpenAI schema to match the original tool schema's parameters and types
        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]