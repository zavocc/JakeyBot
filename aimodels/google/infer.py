from .config import ModelParams
from core.ai.core import Utils
from core.exceptions import CustomErrorMessage
from google import genai
from google.genai import types
import aiohttp
import discord

class Completions(ModelParams):
    def __init__(self, model_name, discord_ctx, discord_bot, guild_id: int = None):
        super().__init__()

        # Discord context
        self._discord_ctx = discord_ctx

        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = self._discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = self._discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        # Check if discord_bot whether if its a subclass of discord.Bot
        if not isinstance(discord_bot, discord.Bot):
            raise Exception("Invalid discord bot object provided")

        # Discord bot object lifecycle instance
        self._discord_bot: discord.Bot = discord_bot

        # Check if _gemini_api_client is in the self._discord_bot object
        if not hasattr(discord_bot, "_gemini_api_client"):
            raise Exception("Gemini API client for completions not initialized, please check the bot configuration")

        # Check if _aiohttp_main_client_session is in the self._discord_bot object
        if not hasattr(discord_bot, "_aiohttp_main_client_session"):
            raise Exception("aiohttp client session for get requests not initialized, please check the bot configuration")

        self._gemini_api_client: genai.Client = discord_bot._gemini_api_client
        self._aiohttp_main_client_session: aiohttp.ClientSession = discord_bot._aiohttp_main_client_session

        self._model_name = model_name
        self._guild_id = guild_id

    ############################
    # Inferencing
    ############################
    # Chat Completion
    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        if _chat_thread is None:
            _chat_thread = []

        # Substitute the system instruction as user prompt
        if system_instruction:
            _chat_thread.append(
                types.Content(
                    parts=[types.Part.from_text(text=system_instruction)],
                    role="user"
                ).model_dump(exclude_unset=True)
            )

        # Parse prompts
        _chat_thread.append(
            types.Content(
                parts=[types.Part.from_text(text=prompt)],
                role="user"
            ).model_dump(exclude_unset=True)
        )
    
        # Create response
        _response = await self._gemini_api_client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                **self._genai_params,
                system_instruction=None,
            )
        )

        # Check if the response was blocked due to safety and other reasons than STOP
        # https://ai.google.dev/api/generate-content#FinishReason
        if _response.candidates[0].finish_reason == "SAFETY":
            raise CustomErrorMessage("🤬 I detected unsafe content in your prompt, Please rephrase your question.")
        elif _response.candidates[0].finish_reason == "MAX_TOKENS":
            raise CustomErrorMessage("⚠️ Response reached max tokens limit, please make your message concise.")
        elif _response.candidates[0].finish_reason != "STOP":
            raise CustomErrorMessage("⚠️ An error has occurred while giving you an answer, please try again later.")
    
        for _part in _response.candidates[0].content.parts:
            if _part.text and _part.text.strip():
                await Utils.send_ai_response(self._discord_ctx, prompt, _part.text, self._discord_method_send)

        # Append the final response to the chat thread
        _chat_thread.append(_response.candidates[0].content.model_dump(exclude_unset=True))

        # Return the status
        return {"response": "OK", "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)
