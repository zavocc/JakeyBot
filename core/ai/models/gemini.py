from core.ai.history import HistoryManagement as histmgmt
from core.ai.tools import BaseFunctions
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from os import environ
import google.generativeai as genai
import asyncio
import google.api_core.exceptions
import inspect

class Gemini:
    def __init__(self,
                 bot, ctx,
                 model_name = "gemini-1.5-flash-001",
                 system_prompt = None, 
                 generation_config = None,
                 safety_settings = None):
        self.ctx = ctx
        self.bot = bot

        self.model = model_name
        if system_prompt is None:
            system_prompt = "You are a helpful assistant"

        # Set the generation configuration if not provided
        if not generation_config and type(generation_config) is not dict:
            generation_config = {}

        # Validate the generation configuration
        if "temperature" not in generation_config:
            generation_config["temperature"] = 0.8

        if "top_p" not in generation_config:
            generation_config["top_p"] = 1

        if "top_k" not in generation_config:
            generation_config["top_k"] = 64

        if "max_output_tokens" not in generation_config:
            generation_config["max_output_tokens"] = 8192

        # Set safety settings if not provided
        if not safety_settings and type(safety_settings) is not dict:
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
            ]

        # Tools definitions
        self.tools_functions = BaseFunctions(bot, ctx)

        # Initialize chat history class
        self._HistoryManagement = histmgmt(ctx.guild.id)

        # Init genai
        genai.configure(api_key=environ.get("GOOGLE_AI_TOKEN"))

        # Configure
        self.client = genai.GenerativeModel(
            model_name=self.model,
            safety_settings=safety_settings,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )

    async def multimodal_handler(self, attachment = None, filename = None):
        if attachment is None:
            raise Exception("No attachment provided, please provide the path to the attachment")
        
        # Upload the attachment to files API
        _file = genai.upload_file(path=attachment, display_name=filename)
        _msgstatus = None

        # Wait for the file to be processed
        while _file.state.name == "PROCESSING":
            if _msgstatus is None:
                _msgstatus = await self.ctx.send("⌛ Processing the file attachment... this may take a while")
                await asyncio.sleep(3)
                _file = genai.get_file(_file.name)

        if _file.state.name == "FAILED":
            await self.ctx.respond("❌ Sorry, I can't process the file attachment. Please try again.")
            raise Exception(_file.state.name)
        
        # Immediately use the "used" status message to indicate that the file API is used
        if _msgstatus is not None:
            await _msgstatus.edit(content=f"Used: **{filename if filename is not None else 'Files API'}**")
        else:
            await self.ctx.send(f"Used: **{filename if filename is not None else 'Files API'}**")

        # Add caution that the attachment data would be lost in 48 hours
        await self.ctx.send("> 📝 **Note:** The submitted file attachment will be deleted from the context after 48 hours.")

        # Return the file object
        return _file
    
    # Chat
    # async def chat_completion_whistory(self, prompt, file = None):
    #     # Load history
    #     try:
    #         await self._HistoryManagement.load_history()
    #     except ValueError:
    #         await self.ctx.respond("⚠️ Maximum history reached! Please wipe the conversation using `/sweep` command")
    #         raise Exception("Maximum history reached! Clear the conversation") 
        
    #     _history = self._HistoryManagement.context_history

    #     # enable plugins
    #     # check if its a code_execution
    #     if (await self._HistoryManagement.get_config()) == "code_execution":
    #         _enabled_tools = "code_execution"
    #     else:
    #         _enabled_tools = getattr(self.tools_functions, (await self._HistoryManagement.get_config()))

    #     # Craft prompt if it has a file
    #     final_prompt = [file, f'{prompt}'] if file is not None else f'{prompt}'
    #     chat_session = self.client.start_chat(history=None)

    #     # Generate completion
    #     try:
    #         _answer = await chat_session.send_message_async(final_prompt, tools=_enabled_tools)
    #     except google.api_core.exceptions.PermissionDenied:
    #         _history["chat_history"] = [
    #             {"role": x.role, "parts": [y.text]} 
    #             for x in chat_session.history 
    #             for y in x.parts 
    #             if x.role and y.text
    #         ]

    #         # Notify the user that the chat session has been re-initialized
    #         await self.ctx.send("> ⚠️ One or more file attachments or tools have been expired, the chat history has been reinitialized!")

    #         # Re-initialize the chat session
    #         chat_session = self.client.start_chat(history=_history["chat_history"])
    #         _answer = await chat_session.send_message_async(final_prompt, tools=_enabled_tools)

    #     # Call tools
    #     # DEBUG: content.parts[0] is the first step message and content.parts[1] is the function calling data that is STOPPED
    #     # print(answer.candidates[0].content)
    #     _candidates = _answer.candidates[0]

    #     if 'function_call' in _candidates.content.parts[-1]:
    #         _func_call = _candidates.content.parts[-1].function_call

    #         # Call the function through their callables with getattr
    #         try:
    #             _result = await getattr(self.tools_functions, f"_callable_{_func_call.name}")(**_func_call.args)
    #         except AttributeError as e:
    #             await self.ctx.respond("⚠️ The chat thread has a feature is not available at the moment, please reset the chat or try again in few minutes")
    #             # Also print the error to the console
    #             raise AttributeError(e)
            
    #         # send it again, and lower safety settings since each message parts may not align with safety settings and can partially block outputs and execution
    #         _answer = await chat_session.send_message_async(
    #             genai.protos.Content(
    #                 parts=[
    #                     genai.protos.Part(
    #                         function_response = genai.protos.FunctionResponse(
    #                             name = _func_call.name,
    #                             response = {"response": _result}
    #                         )
    #                     )
    #                 ]
    #             ),
    #             safety_settings={
    #                 HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    #                 HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    #                 HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    #                 HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
    #             }
    #         )

    #         await self.ctx.send(f"Used: **{_func_call.name}**")

    #     # Append the prompt to prompts history
    #     _history["prompt_history"].append(prompt)
    #     # Also save the ChatSession.history attribute to the context history chat history key so it will be saved through pickle
    #     _history["chat_history"] = chat_session.history

    #     # Print context size and model info
    #     await self._HistoryManagement.save_history()
    #     await self.ctx.send(inspect.cleandoc(f"""
    #                 > 📃 Context size: **{len(_history["prompt_history"])}** of {environ.get("MAX_CONTEXT_HISTORY", 20)}
    #                 > ✨ Model used: **{self.model}**
    #                 """))
            
    #     # Return the response
    #     return _answer.text
    
    async def chat_completion(self, prompt, file = None):
        # Craft prompt if it has a file
        final_prompt = [file, f'{prompt}'] if file is not None else f'{prompt}'
        chat_session = self.client.start_chat(history=None)

        # Generate completion
        _answer = await chat_session.send_message_async(final_prompt, tools="code_execution")

        # Print context size and model info
        await self._HistoryManagement.save_history()
        await self.ctx.send(inspect.cleandoc(f"""
                    > 📃 History will be back! Stay tuned!
                    > ✨ Model used: **{self.model}**
                    """))
            
        # Return the response
        return _answer.text