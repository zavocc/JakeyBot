from google.genai import types
import aiohttp
import datetime
import discord
import google.genai as genai
import io

class Tool:
    tool_human_name = "Image Generation and Editing"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
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

    # Image generator
    async def _tool_function(self, prompt: str, temperature: int = 0.7, discord_attachment_url: str = None, text_controls: str = "NONE"):
        # Create image
        _message_curent = await self.method_send(f"⌛ Generating with prompt **{prompt}**... this may take few minutes")
        
        # Check if global aiohttp and google genai client session is initialized
        if not hasattr(self.discord_bot, "_gemini_api_client"):
            raise Exception("gemini api client isn't set up, please check the bot configuration")
        
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _api_client: genai.Client = self.discord_bot._gemini_api_client
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session

        # Craft prompts
        _prompt = [prompt]

        if text_controls == "INTERLEAVE_TEXT":
            _prompt.append("By the way, also output text during the generation process")
        elif text_controls == "EXPLAIN_PROCESS":
            _prompt.append("Please explain your image generation process or reasoning then generate the image")
        elif text_controls == "ITERATIVE_LOOP":
            _prompt.append("By the way, you must continously refine the generated image until it looks right based on the prompt")

        # Download the image if needed        
        # We need to check the file size
        if discord_attachment_url:
            async with _client_session.head(url=discord_attachment_url) as _response:
                _content_length = int(_response.headers.get("Content-Length", 0))

                if _content_length == 0:
                    raise ValueError("The image size is zero or invalid, please provide a valid image")
                
                # Check if the mime type is image
                _mime_type = _response.headers.get("Content-Type", None)
                if not _mime_type or not _mime_type.startswith("image"):
                    raise ValueError("The file is not an image, please provide an image file")

                if _content_length > 3 * 1024 * 1024:
                    raise ValueError("The image size is too large, please provide an image that is less than 3MB")
                
            # Download the image
            async with _client_session.get(discord_attachment_url) as _response:
                _imagedata = await _response.read()

            _prompt.append(types.Part.from_bytes(data=_imagedata, mime_type=_mime_type))

        # Generate response
        _response = await _api_client.aio.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=[_prompt],
            config={
                "response_modalities": ["Text", "Image"],
                "candidate_count": 1,
                "temperature": temperature,
                "max_output_tokens": 8192
            }
        )

        if _response.candidates[0].finish_reason == "IMAGE_SAFETY":
            raise ValueError("The image is blocked by the filter, try again")

        # ResponseRM
        _gemini_responses = {
            "status": "IMAGE_GENERATION_SUCCESS",
            "additionalMetadata": "Here are responses generated by Gemini during generation process, this is only used for debugging purposes so only use this if the model spits out errors like refusals. Do not send this to the end users",
            "additionalInstructions": "DO NOT present te Gemini responses to end users!!! These texts are already sent",
            "responsesLogs": [],
            "generatedImagesURL": []
        }

        # Send the image
        for _index, _parts in enumerate(_response.candidates[0].content.parts):
            if _parts.text:
                _gemini_responses["responsesDebug"].append(_parts.text)
                await self.method_send(f"{_parts.text[:2000]}")

            if _parts.inline_data:
                # HH_MM_SS_MMDDYYYY_EPOCH
                _file_format = datetime.datetime.now().strftime("%H_%M_%S_%m%d%Y_%s")

                 # Send the image
                _files = await self.method_send(file=discord.File(fp=io.BytesIO(_parts.inline_data.data), filename=f"generated_image{_file_format}_image_part{_index}.png"))
                _gemini_responses["generatedImagesURL"].append(
                    {
                        "generatedImageDiscordURL": _files.attachments[0].url,
                        "fileName": _files.attachments[0].filename,
                        "createdTime": _file_format,
                        "index": _index
                    }
                )

        # Delete status
        await _message_curent.delete()

        # Cleanup
        return _gemini_responses