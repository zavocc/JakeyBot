# ToC
- [ToC](#toc)
- [JakeyBot Tools](#jakeybot-tools)
  - [Using Tools](#using-tools)
  - [Opting out of Tools](#opting-out-of-tools)
  - [Limitations](#limitations)
  - [Forking and development (for developers)](#forking-and-development-for-developers)
    - [Step 1: Creating your tool outline](#step-1-creating-your-tool-outline)
    - [Step 2: Registering your tools](#step-2-registering-your-tools)
    - [Step 3: Making your tool visible to Discord UI](#step-3-making-your-tool-visible-to-discord-ui)

# JakeyBot Tools
JakeyBot has tools that connects to the outside world and call functions outside text generation process. It is similar to [ChatGPT plugins](https://openai.com/index/chatgpt-plugins/) or [Gemini Extensions](https://support.google.com/gemini/answer/13695044) extending the functionality of the JakeyBot beyond its purpose.

It uses [Function calling](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb) under the hood, whenever you ask Jakey a specific question that relates to calling specific function, it can intelligently call function by passing the function name and argument from the schema during text completion process and call a function to fulfill a specific task or ground its response.

Jakey already has few tools since its initial implementation, first-party built-in tools include:
- Code execution (default) - Executes Python code and performs calculations but it cannot exchange unstructured data, this has been used by default before Jakey Tools are implemented.
- Image generation with Stable Diffusion 3 - Calls Huggingface spaces endpoints to generate an image within using the space from [stabilityai/stable-diffusion-3-medium](https://huggingface.co/spaces/stabilityai/stable-diffusion-3-medium) but the model can only pass `prompt`, `width` and `height` parameters unlike `/imagine` command and caps to 1344x1344 resolution at max. Since we're using public space endpoints, this is much slower than managed plans. This tool sends the image output to the current Discord thread where you have the permission or Jakey to send messages.
- Random Reddit - This is a simple tool to fetch random posts with images from subreddits of your choice.
- Web Browsing with DuckDuckGo - Simple web search using DuckDuckGo and scrapes webpage contents to augument responses with Jakey. This only supports upto 6 webpages max with "li", "ul", "p" and "article" elements for now.
- YouTube Search - When enabled, the model can search for videos based on your request and extract video metadata from YouTube if you provided a YouTube URL.

Using these Tools is in currently beta and is subject to change, you agree that your chats may not always call the tool correctly.

When the tool is used whether if its successful or failed, an interstitial will be shown below the response body if the particular tool is used.

In case Jakey fabricates its response and does not call the tools (and does not show an interstitial status). You can either manually tell the model to call the tool or clear the chat history to fully take effect since chat history can affect how it calls tools.

## Using Tools
Existing chat history defaults to Code Execution (`code_execution`). To activate tools, use the `/feature` command which only accepts one argument which you can choose to select a particular tool. Keep in mind that you can use one tool at a time per chat thread and changing features will **clear your chat history** without warning!

If you already enabled particular tool and re-ran the command with the same tool that is being used, it won't clear the chat history.

## Opting out of Tools
The only way to opt out of tools is to use Code Execution. Since its a native capability from Gemini API and does not show interstitial when used in any way. Having this capability always enabled reduces the model to fabricate calculations and make output assumptions from Python code. But code execution cannot be used with other tools at the same time

## Limitations
- Jakey may not always call the tool especially on first conversation. You can always explicitly ask Jakey a follow up question to use that particular feature (e.g. "Search it using YouTube tool"), refine your prompt, or clear your chat history (as it may influence how it should call tools). For best results, its suggested to use the 1.5 Pro model to better call function automatically in some cases.
- Any unstructured data (e.g. attachments) cannot be passed within functions as [the schema only allows certain input and output types](https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/protos/Type.md) and preferrably inline input parameters (subject to change as more tools are going to be implemented). 

    While output data is still limited to supported types mentioned, all of the unstructured data outputs can utilize Discord API (pycord) inside the function for yielding the result by sending the attachment and the only data that is going to be returned to the model is the result/status. Meaning, the model has no idea what it actually outputs and only assumes whether if it was successful or not.
- Only one tool can be used at a time.

## Forking and development (for developers)
> ⚠️ CAUTION: This documentation will change at anytime as Tools are in beta, follow at your own risk! If you don't know what you're doing and you just want to request new tool or feature, just create a new issue from this repository.
> 
> Syntax and the structure of this code are subject to change.
>
> in the future, we can think of ways to simplify these process (e.g. JSON or YAML based registration)
>
> Due to the complexity of this documentation, use this as a guide than a step-by-step tutorial.

When forking or creating a PR to add and integrate your function or tool, you must follow the guidelines how to add your tools

Files involved:
- `cogs/gemini/chat_mgmt.py`
- `core/ai/tools.py`
- `tools/*.py`

For inspiration, you can refer to the files above.

It is recommended to have some Python knowledge involving OOP, functions and asynchronous programming, including the [Gemini API function calling](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb#Manual_Function_Calling) and some Discord API in python knowledge (pycord) when dealing with unstructured data output or Discord-related interactions. If you want to request tool ideas, you can instead create an issue.

### Step 1: Creating your tool outline
All tools along with their implementation are in `tools/` directory within project's root. Its recommended and suggested to declare your tools in a new Python file (as module).

The outline of your tools (`tools/example.py`):
```py
import google.generativeai as genai # required
import discord # optional

# This is where you can declare your all your tools information to be converted as schema. The function you're declaring must have an implementation (python function)
class ToolsDefinitions:
    # Multiply
    multiply = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                # the model will understand the name, description, and parameters
                # For best result, choose a descriptive but not conflicting name and concise description.
                name = "multiply",
                description = "Multiply numbers",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        # See https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/protos/Type.md for supported types

                        # When dealing with multiline strings, its recommended to chunk them or consolidate them into single line of string. Since it can trigger 500 errors (if grpc transport is used) and escape sequences may not be passed correctly. WIP to sanitize data properly within /cogs/gemini/genai.py#ask.
                        'a':genai.protos.Schema(type=genai.protos.Type.NUMBER),
                        'b':genai.protos.Schema(type=genai.protos.Type.NUMBER)
                        # Optional
                        'c':genai.protos.Schema(type=genai.protos.Type.NUMBER)
                    },
                    required=['a', 'b'] # If having optional parameters, you must have default value in your function signature and it should be named parameters in ORDER from required -> optional with default values.
                )
            )
        ]
    )


# This extends ToolsDefinitions
# While technically the above class may not be necessarily need inheritance and directly putting them all here in this class is valid. It organizes the code this way.
# This is where
class ToolImpl(ToolsDefinitions):
    # The init constructor
    # If your functions doesnt need to interact with Discord (using discord.ext.commands.Context and discord.bot), you can remove this constructor.
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

    # All functions must be in async even if there's nothing to be awaited, and all functions must have a return statement

    # The signature must be in order according to the schema
    # and the method name must not be the same as attribute name from the schema to prevent confusion
    async def _multiply(self, a, b, c):
        # Return types must be from the supported types as
        # https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/protos/Type.md
        return a*b*c
```
Recommendations:
- Its recommended to handle errors with try-except block and return the status as string if the operation was failed or successful. Since, it is still being executed normally inside [`cogs/gemini/genai.py`](../cogs/gemini/genai.py#L226) and whatever exception occured inside the tool function can affect the execution of `/ask` command as a whole, causing partial execution.

For unpredictable errors, you can use the `except Exception as e` clause inside your function and tell the model the reason for context
```python
try:
    heavylifting_ops_here()
except Exception as e:
    return f"An error has occured, reason: {e}"
```
Error handling is going to be improved in the future.

- For yielding unstructured data (e.g. generated audio, images, video, or document files), you can use the 
```python
await self.ctx.send(file=discord.File(fp="<file path or file-like object>"))
```

Please see: https://docs.pycord.dev/en/stable/ext/commands/api.html#discord.ext.commands.Context.send

- If your function needs external python dependencies, please use `importlib` to programatically and dynamically import modules when needed. So it doesn't depend with JakeyBot, and return an error message to the model if it wasn't installed. One way to do so in your function is:
```python
try:
    gradio_client = importlib.import_module("gradio_client")
    os = importlib.import_module("os")
except ModuleNotFoundError:
    return "This tool is not available at the moment"
```

### Step 2: Registering your tools
Once you created your own tool with necessary function implmenetations on how your tool works. Register your tools in [`core/ai/tools.py`](../core/ai/tools.py) which uses compositions
```python
import tools.example

# This class is used to call functions in cogs/gemini.genai.py
class BaseFunctions:
    def __init__(self, bot, ctx):
        # From tools/example.py within ToolImpl class inherited from ToolsDefinitions class
        self.example = tools.example.ToolImpl(bot, ctx)

        # self.<ModuleName>.<FunctionToolName>
        # This is from the ToolsDefinitions class as the Gemini API will parse the schema
        self.multiply = self.example.multiply
        

    # Tool methods, the signature must be in order according to the schema
    # required -> optional with defaults (for optional arguments, you must provide defaults)
    #
    # Must be in this syntax and the method name must exactly start with _callable_ and your function name
    # _callable_yourtoolname
    #
    # You just need to specify your function name and signature with default values for optional params in order
    async def _callable_multiply(self, a, b, c = 1):
        return await self.example._multiply(a, b, c)
```

### Step 3: Making your tool visible to Discord UI
The last step is to make it visble to Discord UI for users to activate the tool.

On the file [`cogs/gemini/chat_mgmt.py`](../cogs/gemini/chat_mgmt.py#L67) within the method `feature` command decorator `@discord.option` and parameter `choices` which accepts `list[str, discord.OptionChoices]`. Format your option as
```python
@discord.option(
    "capability",
    description = "Integrate tools to chat! Setting chat features will clear your history!",
    choices=[
        discord.OptionChoice("Human readable description about your tool", "tool_name_from_schema")
    ]
)
```
In this example's case. It would be
```python
choices=[
    discord.OptionChoice("Multiply numbers", "multiply")
]
```
