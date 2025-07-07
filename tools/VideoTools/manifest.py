class ToolManifest:
    tool_human_name = "Video Generation"

    def __init__(self):
        self.tool_schema = [ 
            {
                "name": "video_generator",
                "description": "Create videos with sounds",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt for the model to generate the video"
                        },
                        "negative_prompt": {
                            "type": "string",
                            "description": "Instruction which to exclude or avoid to be put in the video"
                        },
                        "enable_audio": {
                            "type": "boolean",
                            "description": "Enable sound in the video. Default is true"
                        },
                        "audio_negative_prompt": {
                            "type": "string",
                            "description": "When audio is enabled, tune the audio of the video by excluding the mentioned sound constraints from the user's query"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration of the video in seconds. Minimum is 5 and maximum is 8 seconds"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]