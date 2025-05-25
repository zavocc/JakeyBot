class ToolManifest:
    tool_human_name = "Image Generation and Editing"
    image_generator_tool_description = "Generate or edit an image with Gemini 2.0 Flash's image generation capabilities"
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
                        "temperature": {
                            "type": "integer",
                            "description": "Parameter for the LLM that controls diversity and variety of the generated content, it's recommended to keep the temp values below 1.2"
                        },
                        "discord_attachment_url": {
                            "type": "string",
                            "description": "The Discord attachment URL for image to be referenced or edited. When editing an image, it's recommended to keep the prompt simple to prevent unnecessary elements being added or deviations as it is a LLM model that is contextually capable at editing images, you do not need to describe the original image as prompt again if the attachment was provided, just prompt the requested changes without adding extra to little info of the image. For example, when a cat image is provided and user asks to edit it to have a hat, just say add a hat."
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
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]