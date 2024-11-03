from core.exceptions import ToolsUnavailable
from os import environ
import discord
import importlib
import json
import logging
import litellm

class Completions:
    _model_provider_thread = "gemini_litellm"

    def __init__(self, guild_id = None, 
                 model_name = "gemini-1.5-flash-002",
                 db_conn = None):
        super().__init__()

        self._file_data = None

        self._model_name = model_name
        self._guild_id = guild_id
        self._history_management = db_conn
        
    async def input_files(self, attachment: discord.Attachment, **kwargs):
        _attachment_prompt = {
            "type":"image_url",
            "image_url": {
                    "url": attachment.url
                }
            }

        self._file_data = _attachment_prompt


    async def chat_completion(self, prompt, system_instruction: str = None):
        # Setup model and tools
        if hasattr(self, "_discord_method_send") and self._history_management is not None:
            try:
                _Tool_use = importlib.import_module(f"tools.{(await self._history_management.get_config(guild_id=self._guild_id))}").Tool(self._discord_method_send)
            except ModuleNotFoundError as e:
                logging.error("I cannot import the tool because the module is not found: %s", e)
                raise ToolsUnavailable

            #if _Tool_use.tool_name == "code_execution":
            #    _Tool_use.tool_schema = "code_execution"
        else:
            _Tool_use = None

        print(_Tool_use.tool_schema_json)

        # Load history
        _chat_thread = await self._history_management.load_history(guild_id=self._guild_id, model_provider=self._model_provider_thread)
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
            model="gemini/" + self._model_name,
            max_tokens=8192,
            temperature=0.7,
            api_key=environ.get("GEMINI_API_KEY"),
            tools=[_Tool_use.tool_schema_json]
        )

        print(_response.choices[0].message.model_dump())

        # Call tools
        _tool_call = _response.choices[0].message.tool_calls
        if _tool_call:
            print(_tool_call[0].function.arguments)

            # Append the response
            _chat_thread.append(_response.choices[0].message.model_dump())

            # Send the first response if possible
            if _response.choices[0].message.content:
                await self._discord_method_send(_response.choices[0].message.content)

            # Call the tool
            # Call the function through their callables with getattr
            try:
                _result = await _Tool_use._tool_function(**json.loads(_tool_call[0].function.arguments))
            except (AttributeError, TypeError) as e:
                # Also print the error to the console
                logging.error("ask command: I think I found a problem related to function calling:", e)
                raise ToolsUnavailable
            # For other exceptions, log the error and add it as part of the chat thread
            except Exception as e:
                # Also print the error to the console
                logging.error("ask command: Something when calling specific tool lately, reason:", e)
                _result = f"⚠️ Something went wrong while executing the tool: {e}, please tell the developer or the user to check console logs"

            # Append to chat thread
            _chat_thread.append({
                "tool_call_id": _tool_call[0].id,
                "role": "tool",
                "name": _tool_call[0].function.name,
                "content": _result,
            })

            # AI response
            _response = await litellm.acompletion(
                messages=_chat_thread,
                model="gemini/" + self._model_name,
                max_tokens=8192,
                temperature=0.7,
                api_key=environ.get("GEMINI_API_KEY"),
            )
            _answer = _response.choices[0].message.content
        else:
            # AI response
            _answer = _response.choices[0].message.content

        # Append to chat thread
        _chat_thread.append(_response.choices[0].message.model_dump())

        return {"answer":_answer, "chat_thread": _chat_thread}

    async def save_to_history(self, chat_thread = None):
        await self._history_management.save_history(guild_id=self._guild_id, chat_thread=chat_thread, model_provider=self._model_provider_thread)