from models.tasks.media.fal_ai import run_video

# Function implementations
class Tools:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Video generator
    async def tool_video_generator(
        self,
        prompt: str,
        url_context: str = None,
        duration: str = "8",
        aspect_ratio: str = "16:9",
    ):
        # THIS IS A BETA RESTRICTED TOOL, we only support bot owner for now
        # Check if the author is the bot owner
        if not (await self.discord_bot.is_owner(self.discord_ctx.author)):
            raise PermissionError("Video generation tool is restricted to the bot owner only.")

        # Create video
        # Interstitial
        _messageInterstitial = await self.discord_ctx.channel.send("📹 **Sora 2** is now generating your video... please check back later and you'll be notified once it's ready.")

        _baseParams = {
            "prompt": prompt,
            "duration": int(duration),
            "aspect_ratio": aspect_ratio,
            "resolution": "720p",
        }
        # Check if we have URL context
        if url_context:
            _model_name = "sora-2/image-to-video"
            _baseParams["image_url"] = url_context
        else:
            _model_name = "sora-2/text-to-video"

        # Generate video
        _videoURL = await run_video(
            model_name=_model_name,
            send_url_only=True,
            **_baseParams
        )

        # Send the video
        await _messageInterstitial.edit(f"✅ Your video is ready, you can download it [here]({_videoURL})")

        return "The video generation is complete and has been sent to the UI.",
