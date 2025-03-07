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
- Disabled - You can disable these tools via `/feature capability:Disabled`

- Artifacts - File generation capability, ask Jakey to write code or markdown files and it will send as said file. Must allow Jakey to send attachments

- Canvas - Ideation and brainstorming tool by creating a new thread focused on particular topic. With content, plan, and optionally code. Requires threads permission granted and must be in DMs

- Code execution - Executes Python code and performs calculations but it cannot exchange unstructured data, this has been used by default before Jakey Tools are implemented.

- Browse with Bing - Grounds responses with search results fetched by Bing, needs atleast one free Azure subscription and you need to choose either Key 1 or Key 2.
  
    You must configure the Bing API key via `BING_SUBSCRIPTION_KEY` from [dev.env](/dev.env.template)

- GitHub - Searches and reasons over GitHub repository files, you can ask Jakey to summarize files from specific repository (e.g. `Summarize this file README.md from zavocc/JakeyBot`)
  
    Self hosting only needs GitHub personal access token with read only public key access.

    Get one at https://github.com/settings/personal-access-tokens with public access

    You must configure GitHub PAT via `GITHUB_TOKEN` from [dev.env](/dev.env.template)

- EzAudio - Edit specific segment of the audio using natural language prompt, provide the audio file to Gemini, specifiy what segment of the sound to be edited (e.g. a honk in the background), and how long that sound should last

    - Dependencies required: `gradio_client`

- Image 2 Line drawing - Convert images to sketches, provide the image, and whether if it's a simple or complex (default) lines. 
  
    - Dependencies required: `gradio_client`
  
- Image generation with Stable Diffusion 3.5 - Calls Huggingface spaces endpoints to generate an image within using the space from [stabilityai/stable-diffusion-3.5-large-turbo](https://huggingface.co/stabilityai/stable-diffusion-3.5-large-turbo).

    You must acquire the Serverless API access token via `HF_TOKEN` with public access from [dev.env](/dev.env.template)

- YouTube Search - When enabled, the model can search for videos based on your request and extract video metadata from YouTube if you provided a YouTube URL.

    You must configure the YouTube Data API v3 key via `YOUTUBE_DATA_v3_API_KEY` from [dev.env](/dev.env.template)

Using these Tools is in currently beta and is subject to change, you agree that your chats may not always call the tool correctly.

When the tool is used whether if its successful or failed, an interstitial will be shown below the response body if the particular tool is used.

In case Jakey fabricates its response and does not call the tools (and does not show an interstitial status). You can either manually tell the model to call the tool or clear the chat history to fully take effect since chat history can affect how it calls tools.

## Using Tools
To activate tools, use the `/feature` command which only accepts one argument which you can choose to select a particular tool. Keep in mind that you can use one tool at a time per chat thread and changing features will **clear your chat history** without warning!

If you already enabled particular tool and re-ran the command with the same tool that is being used, it won't clear the chat history.

## Opting out of Tools
Please set `/feature capability:Disabled` to opt out.

## Limitations
- One tool can be used at a time per chat thread. You cannot use multiple tools at the moment.

- Tools only supports Gemini models

- It's recommended to use Gemini 2.0 as it's specifically optimized for tool usage so a zero-shot prompting is enough to understand your intent and call tools. Gemini 1.5 models also work but they may require to explicitly call tools
