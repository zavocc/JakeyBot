from models.tasks.media.fal_ai import run_video
from os import environ


# Function implementations
class Tools:
    def __init__(self, discord_ctx, discord_bot):
        self.discord_ctx = discord_ctx
        self.discord_bot = discord_bot

    # Video generator
    async def tool_video_generator(
        self,
        prompt: str,
        duration: str = "8",
        aspect_ratio: str = "16:9",
    ):
        # Create video
        # Interstitial
        _messageInterstitial = await self.discord_ctx.channel.send("📹 **Sora 2** is now generating your video... please check back later and you'll be notified once it's ready.")

        # Generate video
        _videoURL = await run_video(
            model_name="sora-2",
            send_url_only=True,
            prompt=prompt,
            duration=int(duration),
            aspect_ratio=aspect_ratio,
            resolution="720p",
        )

        # Send the video
        await _messageInterstitial.edit(f"✅ Your video is ready, you can download it [here]({_videoURL})")

        return "The video generation is complete and has been sent to the UI.",
