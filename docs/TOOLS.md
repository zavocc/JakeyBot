# ToC
- [ToC](#toc)
- [JakeyBot Tools](#jakeybot-tools)
  - [Using Tools](#using-tools)
  - [Opting out of Tools](#opting-out-of-tools)
  - [Limitations](#limitations)

# JakeyBot Tools
JakeyBot has tools that connects to the outside world and call functions outside text generation process. It is similar to [ChatGPT plugins](https://openai.com/index/chatgpt-plugins/) or [Gemini Extensions](https://support.google.com/gemini/answer/13695044) extending the functionality of the JakeyBot beyond its purpose.

It uses [Function calling](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb) under the hood, whenever you ask Jakey a specific question that relates to calling specific function, it can intelligently call function by passing the function name and argument from the schema during text completion process and call a function to fulfill a specific task or ground its response.

Jakey already has few tools since its initial implementation, first-party built-in tools include:
- Code execution (default) - Executes Python code and performs calculations but it cannot exchange unstructured data, this has been used by default before Jakey Tools are implemented.

- Browse with Bing - Grounds responses with search results fetched by Bing, needs atleast one free Azure subscription and you need to choose either Key 1 or Key 2.

- GitHub - Searches and reasons over GitHub repository files, you can ask Jakey to summarize files from specific repository (e.g. `Summarize this file README.md from zavocc/JakeyBot`) \
Self hosting only needs GitHub personal access token with read only public key access

- Google Search - Grounds responses with search results fetched by Google, refer to https://developers.google.com/custom-search/v1/introduction to get your own CXID and API Key from Google Cloud
    There are two modes of Grounding:
    1. Simple grounding - performs single query and fetches first 1-10 results
    2. Deep search grounding - takes multiple queries and iteratively fetches results
Keep in mind that the latter can quickly hit daily rate limits on free tier.

- EzAudio - Edit specific segment of the audio using natural language prompt, provide the audio file to Gemini, specifiy what segment of the sound to be edited (e.g. a honk in the background), and how long that sound should last

    Dependencies required: `gradio_client`

- Image 2 Line drawing - Convert images to sketches, provide the image, and whether if it's a simple or complex (default) lines. 
  
    - Dependencies required: `gradio_client`
  
- Image generation with Stable Diffusion 3.5 - Calls Huggingface spaces endpoints to generate an image within using the space from [stabilityai/stable-diffusion-3.5-large](https://huggingface.co/spaces/stabilityai/stable-diffusion-3-large) but the model can only pass `prompt`, `width` and `height` parameters unlike `/imagine` command and caps to 1024x1024 resolution at max. Since we're using public space endpoints, this is much slower than dedicated solutions. This tool sends the image output to the current Discord thread where you have the permission or Jakey to send messages.

    - Dependencies required: `gradio_client`

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
- Tools only supports Gemini models

- It's recommended to use Gemini 2.0 as it's specifically optimized for tool usage so a zero-shot prompting is enough to understand your intent and call tools. Gemini 1.5 models also work but they may require to explicitly call tools
