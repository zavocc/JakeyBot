from os import environ
import aiohttp
import aiofiles
import asyncio
import discord
import io

# Function implementations
class Tool:
    tool_human_name = "Video Generation with Veo 2"
    def __init__(self, method_send, discord_ctx, discord_bot):
        self.method_send = method_send
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

        self.tool_schema = [
            {
                "name": "video_gen_veo",
                "description": "Create high quality videos using Google's Veo 2",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "video_prompt": {
                            "type": "STRING",
                            "description": "Prompt for video to be generated"
                        },
                        "duration": {
                            "type": "STRING",
                            "description": "Duration of the video to be generated, it's recommended to default it to 5.",
                            "enum": ["5s", "6s", "7s", "8s"]
                        },
                    },
                    "required": ["video_prompt"]
                }
            }
        ]

    async def _tool_function(self, video_prompt: str, duration: str = "5s"):
        # Load the "allowlist.yaml" file
        # Returns as list of user IDs
        async with aiofiles.open("allowlist.yaml", mode="r") as _file:
            _allowlist = await _file.read()

        # Early access, only the users from allowlist can use this tool
        if not any([str(self.discord_ctx.author.id) in _allowlist]):
            raise ValueError("You have access to the video generation model but the user you're interacting does not, this is a private preview access model with only certain Discord users under allowlist can use it")

        # Check if FAL_KEY is set
        if not environ.get("FAL_KEY"):
            raise ValueError("FAL.AI API token is not set, please set it in the environment variables")

        # Create video
        message_curent = await self.method_send(f"⌛ Generating **{video_prompt}**... Veo2 is a private preview video model, this may take a while to put you in queue and generate video, please come back later.")
        
        # Check if global aiohttp client session is initialized
        if not hasattr(self.discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")
        
        _client_session: aiohttp.ClientSession = self.discord_bot._aiohttp_main_client_session
        
        # Payload
        _payload = {
            "prompt": video_prompt,
            "aspect_ratio": "16:9",
            "duration": duration,
        }


        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Key {environ.get('FAL_KEY')}"
        }

        # Make a request
        async with _client_session.post("https://queue.fal.run/fal-ai/veo2", json=_payload, headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate video with code {_response.status}, reason: {_response.reason}")
            
            # Get the request ID
            _status = await _response.json()

        # We need to loop through the status endpoint until it is completed
        while True:
            async with _client_session.get(f"https://queue.fal.run/fal-ai/veo2/requests/{_status['request_id']}/status", headers=_headers) as _response:
                # Error code beyond 202 is not successful
                if _response.status > 202:
                    raise Exception(f"Failed to generate video with code {_response.status}, reason: {_response.reason}")
                
                # Send the video
                _status = await _response.json()

                # Check if we can deserialize it
                if _status["status"] == "COMPLETED":
                    break

                # Wait for 2.5 seconds
                await asyncio.sleep(2.5)

        # Get the video
        async with _client_session.get(f"https://queue.fal.run/fal-ai/veo2/requests/{_status["request_id"]}", headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate video with code {_response.status}, reason: {_response.reason}")
            
            # Send the video
            _status = await _response.json()

            # Check if we can deserialize it
            if not _status.get("video"):
                raise Exception("Failed to generate video, no videos had been generated")

        # Ensure it is sent as video
        _headers.pop("Content-Type")

        # Download the video
        async with _client_session.get(_status["video"]["url"], headers=_headers) as _response:
            if _response.status > 202:
                raise Exception(f"Failed to generate video with code {_response.status}, reason: {_response.reason}")
            
            # Send the video
            _videodata = await _response.content.read()
        
        # Delete status
        await message_curent.delete()

        # Send the video
        await self.method_send(file=discord.File(fp=io.BytesIO(_videodata), filename="generated_video.mp4"))

        # Cleanup
        return "video generation success and the file should be sent automatically"