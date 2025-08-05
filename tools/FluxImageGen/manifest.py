class ToolManifest:
    tool_human_name = "Image Generation and Editing"
    image_generator_tool_description = "Generate or edit an image with Flux Kontext Pro"
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
                            "description": "The prompt for Flux Kontext Pro to generate or edit the image, when editing the image, you can use prefix like 'Edit this image'."
                        },
                        "discord_attachment_url": {
                            "type": "string",
                            "description": "The Discord attachment URL for image to be referenced or edited. When editing an image, it's recommended to keep the prompt simple to prevent unnecessary elements being added or deviations as it is a LLM model that is contextually capable at editing images, you do not need to describe the original image as prompt again if the attachment was provided, just prompt the requested changes without adding extra to little info of the image. For example, when a cat image is provided and user asks to edit it to have a hat, just say add a hat."
                        },
                        "size": {
                            "type": "string",
                            "enum": ["1024x1024", "1024x1792", "1792x1024"],
                            "description": "The size of the image to be generated. Default is 1024x1024."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]

        self.tool_schema_openai = [
            {"type": "function", "function": _schema} for _schema in self.tool_schema
        ]