class ToolManifest:
    tool_human_name = "GitHub"
    github_file_tool_description = "Retrieve file content from a GitHub repository or set of files, brainstorm and debug code."
    github_search_tool_description = "Search for code, commits, repositories, issues and PRs on GitHub."
    def __init__(self):
        self.tool_schema = [
            {
                "name": "github_file_tool",
                "description": self.github_file_tool_description,
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
                "description": self.github_search_tool_description,
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
            }
        ]

        self.tool_schema_openai = [
            {
                "type": "function",
                "function": {
                    "name": "github_file_tool",
                    "description": self.github_file_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "The file paths to retrieve from the repository. Must start with /"
                            },
                            "repo": {
                                "type": "string",
                                "description": "The repository in the format owner/repo"
                            },
                            "branch": {
                                "type": "string",
                                "description": "The branch name, default is master"
                            }
                        },
                        "required": ["files", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "github_search_tool",
                    "description": self.github_search_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_type": {
                                "type": "string",
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
                                "type": "string",
                                "description": "The search query to search for, you can use search qualifiers, the character limit is 256"
                            },
                            "page": {
                                "type": "integer",
                                "description": "Pagination, default is 1. You can paginate for more results"
                            }
                        },
                        "required": ["search_type", "query"]
                    }
                }
            }
        ]