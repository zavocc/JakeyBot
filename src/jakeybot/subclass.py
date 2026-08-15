from typing import override

import aiohttp
import discord
import google.genai
import openai


class SCJakeyBot(discord.Bot):
    # Run services
    async def service_register(self) -> None:
        self.csession_aiohttp: aiohttp.ClientSession = aiohttp.ClientSession(loop=self.loop)
        self.csession_google: google.genai.Client = google.genai.Client()
        self.csession_openai: openai.Client = openai.Client()

    async def cleanup_services(self) -> None:
        await self.csession_aiohttp.close()

    @override
    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.service_register()
        return await super().start(token, reconnect=reconnect)

    @override
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
