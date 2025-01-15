import aiohttp
import discord
import io
from datetime import datetime
from os import environ
class Tool:
    tool_human_name = "Ideation Tools"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "canvas",
                "description": "Ideate, brainstorm, and create draft content inside Discord thread to continue conversation with specified topic and content",
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
                "description": "Create convenient downloadable artifacts when writing code, markdown, text, or any other human readable content. When enabled, responses with code snippets and other things that demands file operations implicit or explictly will be saved as artifacts as Discord attachment.",
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
            },
            {
                "name": "events",
                "description": "Create tasks and events for the server",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {
                            "type": "STRING",
                            "description": "The name of the event"
                        },
                        "description": {
                            "type": "STRING",
                            "description": "The description of the event"
                        },
                        "start_time": {
                            "type": "STRING",
                            "description": "The start time of the event. You must use the format YYYY-MM-DD HH:MM:SS but also accept the user's request with their date and time format but you should use the given format to create the event. Default is today's date and time"
                        },
                        "end_time": {
                            "type": "STRING",
                            "description": "The end time of the event. You must use the format YYYY-MM-DD HH:MM:SS but also accept the user's request with their date and time format but you should use the given format to create the event. The end time must be future compared to start time"
                        },
                        "location": {
                            "type": "STRING",
                            "description": "The specified location of the event"
                        },
                        "image_prompt": {
                            "type": "STRING",
                            "description": "The optional image prompt for the event for visuals"
                        }
                    },
                    "required": ["name", "description", "start_time", "end_time"]
                }
            }
        ]

    async def _supplementary_image_generator(self, image_description: str):
        # Check if HF_TOKEN is set
        if not environ.get("HF_TOKEN"):
            raise ValueError("HuggingFace API token is not set, please set it in the environment variables")
                
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Payload
        _payload = {
            "inputs": image_description,
        }

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {environ.get('HF_TOKEN')}"
        }

        # Make a request
        async with _client_session.post("https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo", json=_payload, headers=_headers) as _response:
            # Check if the response is not 200 which may print JSON
            # Response 200 would return the binary image
            if _response.status != 200:
                raise Exception(f"Failed to generate image with code {_response.status}, reason: {_response.reason}")
            
            # Send the image
            _imagedata = await _response.content.read()

        return _imagedata
    
    async def _tool_function_canvas(self, thread_title: str, plan: str, content: str, code: str = None, todos: list = None):
        # Check if we're in a server
        if not self.discord_ctx.guild:
            raise Exception("This tool can only be used in a server")

        # Create a new thread
        _msgstarter = await self.discord_ctx.channel.send(f"📃 Planning **{thread_title}**")
        _thread = await _msgstarter.create_thread(name=thread_title, auto_archive_duration=1440)

        # Send the plan
        # Encode and decode using bytes and later decode it again using string escape
        await _thread.send(f"**Plan:**\n{plan}")
        # Send the content
        await _thread.send(f"**Content:**\n{content}")
        # Send the code if available
        if code:
            await _thread.send(f"**Code:**\n```{code}```")
        # Send the todos if available
        if todos:
            await _thread.send(f"**Todos:**\n")
            for _todo in todos:
                await _thread.send(f"- {_todo}")

        return "Thread created successfully"

    async def _tool_function_artifacts(self, file_contents: str, file_name: str):
        # Send the file
        await self.method_send(file=discord.File(io.StringIO(file_contents), file_name))

        return f"Artifact {file_name} created successfully"
    
    async def _tool_function_events(self, name: str, description: str, start_time: str, end_time: str, location: str = "Online", image_prompt: str = None):
        # Check if we're in a server
        if not self.discord_ctx.guild:
            raise Exception("This tool can only be used in a server")
        
        # Parse datetime strings to datetime objects
        _start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        _end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
       
        
        # Construct params
        _params = {
            "name": name,
            "description": description,
            "start_time": _start_time,
            "end_time": _end_time,
        }

        if location:
            _params["location"] = location

        # Generate the image prompt if available
        if image_prompt:
            await self.method_send(f"⌛ Generating **{image_prompt}** for the event")
            _imagedata = await self._supplementary_image_generator(image_prompt)

            # Add the image to params
            _params["image"] = _imagedata

        # Create the event
        await self.discord_ctx.guild.create_scheduled_event(
            **_params
        )

        return f"Event {name} created successfully"