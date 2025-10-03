# ToC
- [ToC](#toc)
- [JakeyBot Agents](#jakeybot-agents)
  - [Agentic capabilities](#agentic-capabilities)
  - [How to register new tools.](#how-to-register-new-tools)
    - [Manifest reference](#manifest-reference)
    - [The base tool class](#the-base-tool-class)
  - [Using Tools](#using-tools)
  - [Opting out of Tools](#opting-out-of-tools)
  - [Limitations](#limitations)

# JakeyBot Agents
JakeyBot has tools which we will call agents that connects to the outside world and call functions outside text generation process. It is similar to [ChatGPT Connectors](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt/) or [Gemini Connected Apps](https://support.google.com/gemini/answer/13695044) extending the functionality of the JakeyBot beyond text generation.

It uses function calling under the hood, whenever you ask Jakey a specific question that relates to calling specific function, it can intelligently call function by passing the function name and argument from the schema during text completion process and call a function to fulfill a specific task or ground its response.

available tools can be viewed [here](../tools/apis/)

## Agentic capabilities
Jakey can iteratively call tools. This means that it doesn't just stop to single tool call, it can autonomously and continously call tools whenever it needs to. For instance, the [Web Search](../tools/apis/InternetSearch) agent has search and browse tool, the models can first browse the web using `web_search` tool, and by interest of viewing and extracting content can automatically call `url_browse` tool based on the web search tool result fed to the context on its reasoning or user's behalf of the request, and if needed, it can conduct additional searches until it's finished.

## How to register new tools.
Tools are located in [/tools/apis](/tools/apis) with validator module named `tools.utils` to parse and call tools based on its schema through the LLM.

Inside of that folder, the structure of the directory is.
```
/tools/apis:
  - ToolNameDirectory
    - manifest.yaml
    - tool.py
```

Without `manifest.yaml`, tools are not registered and shown in `/agent` slash command.

### Manifest reference
The manifest is a YAML file that defines the function name and argument.

The manifest syntax is:
```yaml
tool_human_name: Multiplication Tool # This will be displayed as user option in `/agent name:Multiplication Tool` associated with the tool
tool_list: # Mapping of the basic OpenAPI schema, keep in mind we only support the subset of the schema. You can define as many mapping of tools as you want
  - name: multiply # The actual function name that will be called
    description: Ensure the description is well-written for model to understand the tool's purpose and intent
    parameters: # Mapping of tool parameters
      type: object
      properties: # Parameters of the function, needed.
        multiplicand: # Parameter name
          type: number # Data type - supports common types including string, number, integer, array, and nested object. You can also define string enums
          description: The multiplicand # An optional description of the parameter for the model to better utilize it.
        multiplier:
          type: number
      required: # Array of required parameters, some parameters that are optional can be omitted. But the optional parameters must have default keyword argument value.
        - multiplicand
        - multiplier
```

### The base tool class
In the `tool.py` this is where the actual code is hosted, the skeletal of this python module must have the class name `Tools` on it with the constructors such as `discord_ctx` and `discord_bot` used to interact with Discord API and the user's application context for sending content to chat:

```python
# tool.py
import discord
class Tools:
    def __init__(self, discord_ctx, discord_bot):
        # Used for sending content, creating threads, or sending reactions to Discord chat UI to the current user's context such as the channel used for the bot to respond.
        self.discord_ctx: discord.ApplicationContext = discord_ctx

        # The Discord Bot object subclass under core.startup with class name SubClassBotPlugServices used to access global attributes set there such as global aiohttp client and the bot's event loop.
        self.discord_bot: discord.Bot = discord_bot

    # When defining methods or functions, it must have tool_ prefix followed by the tool function name as defined in schema. The method must be async and returns string, dict, array, or number! 
    # 
    # For non text content needed to be sent in Discord UI. Use the `self.discord_ctx.channel.send(file=discord.File())` function
    async def multiply(self, multiplicand, multiplier):
      return multiplicand * multiplier
```


## Using Tools
To activate tools, use the `/agent` command which only accepts one argument which you can choose to select a particular tool. Keep in mind that you can use one tool at a time per chat thread and changing features will **clear your chat history** without warning!

If you already enabled particular tool and re-ran the command with the same tool that is being used, it won't clear the chat history.

## Opting out of Tools
Please set `/agent name:Disabled` to disable the model from ever calling any tools.

## Limitations
- You cannot activate multiple agents. And switching agents requires chat history to be cleared.
- MCPs are currently not supported as the way how MCP works and how Jakey handles tools is it needs to have a client connection open throughout the execution lifecycle (if using `mcp` python package from anthropic to create a client) and lot of parsing needed for some SDKs that may handle MCP tools differently. An experimental `mcp-experimental` branch that uses FastMCP with remote tools support shows progress but doesn't work correctly in the Gemini SDK if not using context managers (as the code from `tools` module is imported but the FastMCP does not properly support non-context manager connection especially for Gemini SDK). The FastMCP connection is also not subclassed as agent preferences is isolated per Discord user.