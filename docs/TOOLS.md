# ToC
- [ToC](#toc)
- [JakeyBot Tools](#jakeybot-tools)
  - [Using Tools](#using-tools)
  - [Opting out of Tools](#opting-out-of-tools)
  - [Limitations](#limitations)
  - [Creating a spec (for developers)](#creating-a-spec-for-developers)
    - [Step 1: Creating your tool spec](#step-1-creating-your-tool-spec)
    - [Step 2: Registering your tools](#step-2-registering-your-tools)

# JakeyBot Tools
JakeyBot has tools that connects to the outside world and call functions outside text generation process. It is similar to [ChatGPT plugins](https://openai.com/index/chatgpt-plugins/) or [Gemini Extensions](https://support.google.com/gemini/answer/13695044) extending the functionality of the JakeyBot beyond its purpose.

It uses [Function calling](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb) under the hood, whenever you ask Jakey a specific question that relates to calling specific function, it can intelligently call function by passing the function name and argument from the schema during text completion process and call a function to fulfill a specific task or ground its response.

Jakey already has few tools since its initial implementation, first-party built-in tools include:
- Code execution (default) - Executes Python code and performs calculations but it cannot exchange unstructured data, this has been used by default before Jakey Tools are implemented.
- Image generation with Stable Diffusion 3 - Calls Huggingface spaces endpoints to generate an image within using the space from [stabilityai/stable-diffusion-3-medium](https://huggingface.co/spaces/stabilityai/stable-diffusion-3-medium) but the model can only pass `prompt`, `width` and `height` parameters unlike `/imagine` command and caps to 1344x1344 resolution at max. Since we're using public space endpoints, this is much slower than dedicated solutions. This tool sends the image output to the current Discord thread where you have the permission or Jakey to send messages.

    Dependencies required: `gradio_client`

- Random Reddit - This is a simple tool to fetch random posts with images from subreddits of your choice.
- Web Browsing with DuckDuckGo - Simple web search using DuckDuckGo and scrapes webpage contents to augument responses with Jakey. This only supports upto 6 webpage query max.

    Dependencies required: `brotli`, `beautifulsoup4`, `chromadb`, `aiohttp`

- YouTube Search - When enabled, the model can search for videos based on your request and extract video metadata from YouTube if you provided a YouTube URL.

    Dependencies required: `yt-dlp`

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

## Creating a spec (for developers)
> ⚠️ CAUTION: This documentation and spec may change at anytime as Tools are in beta, follow at your own risk! If you don't know what you're doing and you just want to request new tool or feature, just create a new issue from this repository.
> 
> this documentation contains the concepts of registering tools, use this as a guide than a step-by-step tutorial.

When forking or creating a PR to add and integrate your function or tool, you must follow the guidelines how to add your tools

Files involved:
- `data/tools.yaml`
- `tools/*.py`

For inspiration, you can refer to the files above.

It is recommended to have some Python knowledge involving OOP, functions and asynchronous programming, including the [Gemini API function calling](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb#Manual_Function_Calling) and some Discord API in python knowledge (pycord) when dealing with unstructured data output or Discord-related interactions. If you want to request tool ideas, you can instead create an issue.

### Step 1: Creating your tool spec
All tools along with their implementation are in `tools/` directory within project's root. Its recommended and suggested to declare your tools in a new Python file (as module).

Example tool: Multiply (`tools/multiply.py`)

> Filename must be the same as function/tool name
```py
import google.generativeai as genai
import importlib

# This is where you can declare your all your tools information to be converted as schema. The function you're declaring must have an implementation (python function)
class Tool:
    tool_human_name = "Multiply numbers" # This will be shown as interstital to indicate the tool is used
    tool_name = "multiply" # Required property
    def __init__(self, bot, ctx):
        # For interacting with current text channel (this init is required, but you don't need to utilize this)
        self.bot = bot
        self.ctx = ctx

        # Schema (required)
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name, # Use self.tool_name
                    description = "Multiply numbers",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'a':genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            'b':genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            'c':genai.protos.Schema(type=genai.protos.Type.INTEGER)
                        },
                        required=['a', 'b']
                    )
                )
            ]
        )
    
    # The function must always be async, for best result, use async compatible libraries!
    async def _tool_function(self, a, b, c = 1):
        return a * b * c
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
The second and final step is to make it visble to Discord UI for users to activate the tool.

On the file [`data/tools.yaml`](/data/tools.yaml). Register your tools definition for the model to use and human readable description of your tool
```yaml
# tool_name is your function name as defined from the schema as the model will use it
# This is also used to "import" the tool from `tools/` directory (as import tools.multiply)
# Please make sure the filename of your tool from tools directory must be the same as this as mentioned above
- tool_name: multiply
# human readable description where the tool choice is visible to Discord UI within the `/feature` command
  ui_name: Muliply with Python
```