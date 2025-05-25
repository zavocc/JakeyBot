class ToolManifest:
    tool_human_name = "Canvas and Artifacts"
    canvas_description = "Ideate, brainstorm, and create draft content inside Discord thread to continue conversation with specified topic and content"
    artifacts_description = "Create convenient downloadable artifacts when writing code, markdown, text, or any other human readable content. When enabled, responses with code snippets and other things that demands file operations implicit or explictly will be saved as artifacts as Discord attachment."
    def __init__(self):
        self.tool_schema = [
            {
                "name": "canvas",
                "description": self.canvas_description,
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
                "description": self.artifacts_description,
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
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]