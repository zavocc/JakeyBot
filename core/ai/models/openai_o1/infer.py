from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "openai_o1"

    def __init__(self, discord_ctx, guild_id = None, 
                 model_name = "o1-mini"):
        # Check if the discord_ctx is either instance of discord.Message or discord.ApplicationContext
        if isinstance(discord_ctx, discord.Message):
            self._discord_method_send = discord_ctx.channel.send
        elif isinstance(discord_ctx, discord.ApplicationContext):
            self._discord_method_send = discord_ctx.send
        else:
            raise Exception("Invalid discord channel context provided")

        self._file_data = None

        if environ.get("OPENAI_API_KEY"):
            # Set endpoint if OPENAI_API_ENDPOINT is set
            if environ.get("OPENAI_API_ENDPOINT"):
                self._oai_endpoint = environ.get("OPENAI_API_ENDPOINT")
                logging.info(f"Using OpenAI API endpoint: {self._oai_endpoint}")
            else:
                self._oai_endpoint = None
                logging.info("Using default OpenAI API endpoint for O1 models")
            self._model_name = "openai/" + model_name
        elif environ.get("OPENROUTER_API_KEY"):
            logging.info("Using OpenRouter API for OpenAI (O1)")
            self._model_name = "openrouter/openai/" + model_name
            self._oai_endpoint = None
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
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=12000,
            base_url=self._oai_endpoint,
            api_key=environ.get("OPENAI_API_KEY")
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