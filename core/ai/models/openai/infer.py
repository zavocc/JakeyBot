from core.exceptions import MultiModalUnavailable, ChatHistoryFull
from os import environ
import discord
import litellm
import logging

class Completions:
    _model_provider_thread = "openai"

    def __init__(self, guild_id = None, 
                 model_name = "gpt-4o-mini",
                 db_conn = None, **kwargs):
        self._file_data = None

        if environ.get("OPENAI_API_KEY"):
            # Set endpoint if OPENAI_API_ENDPOINT is set
            if environ.get("OPENAI_API_ENDPOINT"):
                self._oai_endpoint = environ.get("OPENAI_API_ENDPOINT")
                logging.info(f"Using OpenAI API endpoint: {self._oai_endpoint}")
            else:
                self._oai_endpoint = None
                logging.info("Using default OpenAI API endpoint")
            self._model_name = "openai/" + model_name
        elif environ.get("OPENROUTER_API_KEY"):
            logging.info("Using OpenRouter API for OpenAI")
            self._model_name = "openrouter/openai/" + model_name
            self._oai_endpoint = None
        else:
            raise ValueError("No OpenAI API key was set, this model isn't available")

        self._guild_id = guild_id
        self._history_management = db_conn

    async def input_files(self, attachment: discord.Attachment, **kwargs):
        # Check if the attachment is an image
        if not attachment.content_type.startswith("image"):
            raise MultiModalUnavailable("Only images are supported for this model")

        _attachment_prompt = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        self._file_data = _attachment_prompt

    async def chat_completion(self, prompt, system_instruction: str = None):
        # Load history
        _prompt_count, _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
        if _prompt_count >= int(environ.get("MAX_CONTEXT_HISTORY", 20)):
            raise ChatHistoryFull("Maximum history reached! Clear the conversation")
        
        if _chat_thread is None:
            # Begin with system prompt
            _chat_thread = [{
                "role": "system",
                "content": system_instruction   
            }]

        
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
            max_tokens=3024,
            temperature=0.7,
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

        return {"answer":_answer, "prompt_count":_prompt_count+1, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None, prompt_count = 0):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, prompt_count=prompt_count, model_provider=self._model_provider_thread)