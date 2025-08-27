class ToolManifest:
    tool_human_name = "Image Generation and Editing"
    image_generator_tool_description = "Contextually generate or edit an image with Gemini 2.5 Flash's image generation capabilities"
    def __init__(self):
        self.tool_schema = [
            {
                "name": "image_generator",
                "description": self.image_generator_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt for Gemini to generate or edit the image."
                        },
                        "url_context": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Array of URLs to add images as part of reference, this can be used for image blending, editing scenarios."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]