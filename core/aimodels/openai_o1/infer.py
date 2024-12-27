from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "openai_o1"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "o1-mini"):
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

        self._file_data = None

        if environ.get("OPENAI_API_KEY"):
            # Set endpoint if OPENAI_API_ENDPOINT is set
            if environ.get("OPENAI_API_ENDPOINT"):
                self._oai_endpoint = environ.get("OPENAI_API_ENDPOINT")
                logging.info("Using OpenAI API endpoint: %s", self._oai_endpoint)
            else:
                self._oai_endpoint = None
                logging.info("Using default OpenAI API endpoint for O1 models")
            self._model_name = "openai/" + model_name
        else:
            raise ValueError("No OpenAI API key was set, this O1 model isn't available")

        self._guild_id = guild_id


    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        if hasattr(self, "_discord_method_send"):
           await self._discord_method_send("🔍 NOTICE: O1 models is a new reasoning engine by OpenAI that is designed to think before it can answer. This model may change, ratelimited, and prematurely respond.")
        
        if _chat_thread is None:
            _chat_thread = []

        
        # Craft prompt
        _chat_thread.append(
             {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        )

        # Check if we have an attachment
        if self._file_data is not None:
            _chat_thread[-1]["content"].append(self._file_data)

        # Generate completion
        litellm.api_key = environ.get("OPENAI_API_KEY")
        if self._oai_endpoint:
            litellm.api_base = self._oai_endpoint
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=12000,
            base_url=self._oai_endpoint,
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": _answer
                    }
                ]
            }
        )

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)