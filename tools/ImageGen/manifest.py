class ToolManifest:
    tool_human_name = "Image Generation and Editing"
    def __init__(self):
        self.tool_schema = self.tool_schema = [
            {
                "name": "image_generator",
                "description": "Generate or edit an image with Gemini 2.0 Flash's image generation capabilities",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "prompt": {
                            "type": "STRING",
                            "description": "The prompt for Gemini to generate or edit the image, it's recommended to keep it elaborate based on user's intent and add a prompt to generate or edit an image"
                        },
                        "temperature": {
                            "type": "INTEGER",
                            "description": "Parameter for the LLM that controls diversity and variety of the generated content, it's recommended to keep the temp values below 1.2"
                        },
                        "discord_attachment_url": {
                            "type": "STRING",
                            "description": "The Discord attachment URL for image to be referenced or edited"
                        },
                        "text_controls": {
                            "type": "STRING",
                            "enum": ["NONE", "INTERLEAVE_TEXT", "EXPLAIN_PROCESS", "ITERATIVE_LOOP"],
                            "description": "Whether to generate text and images. For storytelling usecases, it's recommended to use INTERLEAVE_TEXT, to ensure stronger performance use EXPLAIN_PROCESS, to ensure the model that can refine it's outputs midway use ITERATIVE_LOOP... You must optimize the prompts based on user's request, because these are just preprompts, you don't need to add redundant instructions."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]

        self.tool_schema_openai = [
            {
                "type": "function",
                "function": {
                    "name": "image_generator",
                    "description": "Generate or edit an image with Gemini 2.0 Flash's image generation capabilities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt for Gemini to generate or edit the image, it's recommended to keep it elaborate based on user's intent and add a prompt to generate or edit an image"
                            },
                            "temperature": {
                                "type": "integer",
                                "description": "Parameter for the LLM that controls diversity and variety of the generated content, it's recommended to keep the temp values below 1.2"
                            },
                            "discord_attachment_url": {
                                "type": "string",
                                "description": "The Discord attachment URL for image to be referenced or edited"
                            },
                            "text_controls": {
                                "type": "string",
                                "enum": ["NONE", "INTERLEAVE_TEXT", "EXPLAIN_PROCESS", "ITERATIVE_LOOP"],
                                "description": "Whether to generate text and images. For storytelling usecases, it's recommended to use INTERLEAVE_TEXT, to ensure stronger performance use EXPLAIN_PROCESS, to ensure the model that can refine it's outputs midway use ITERATIVE_LOOP... You must optimize the prompts based on user's request, because these are just preprompts, you don't need to add redundant instructions."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]