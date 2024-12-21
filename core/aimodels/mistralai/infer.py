from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "mistralai"

    def __init__(self, discord_ctx, discord_bot, guild_id = None, model_name = "mistral-large-2407"):
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
        
        if environ.get("MISTRAL_API_KEY"):
            logging.info("Using default Mistral API endpoint")
            self._model_name = "mistral/" + model_name
            logging.info("Using normalized model name: %s", self._model_name)
        else:
            raise ValueError("No Mistral API key was set, this model isn't available")

        self._guild_id = guild_id

    async def chat_completion(self, prompt, db_conn, system_instruction: str = None):
        # Load history
        _chat_thread = await db_conn.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)

        # System prompt
        # Check if codestral model is used since it's not necessary to put system instructions as its designed for code
        # And to prevent tokens from being depleted quickly
        if _chat_thread is None:
            _chat_thread = [{
                "role": "system",
                "content": system_instruction   
            }]
    
        # User prompt
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

        # Generate completion
        _response = await litellm.acompletion(
            messages=_chat_thread,
            model=self._model_name,
            max_tokens=3024,
            temperature=0.7,
            api_key=environ.get("MISTRAL_API_KEY")
        )

        # AI response
        _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(
            {
                "role": "assistant",
                "content": _answer
            }
        )

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, db_conn, chat_thread = None):
        await db_conn.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)