import aiohttp
import discord
import google.genai
import openai


class SCJakeyBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Run services
    async def service_register(self) -> None:
        self.csession_aiohttp = aiohttp.ClientSession(loop=self.loop)
        self.csession_google = google.genai.Client()
        self.csession_openai = openai.Client()

    async def cleanup_services(self) -> None:
        await self.csession_aiohttp.close()

    async def start(self, *args, **kwargs) -> None:
        await self.service_register()
        return await super().start(*args, **kwargs)

    async def close(self) -> None:
        try:
            await self.cleanup_services()
            self.csession_google.close()
            self.csession_openai.close()
        except Exception as e: # noqa: BLE001
            # TODO: swap logging
            print(f"Error during cleanup: {e}")
        print("Closing session")
        await super().close()

    async def on_ready(self):
        print(f"{self.user} is ready and online!")
