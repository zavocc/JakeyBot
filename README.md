- [Jakey Bot](#jakey-bot)
  - [Platform availability](#platform-availability)
  - [Features](#features)
- [Installation and setup](#installation-and-setup)
  - [Required permissions for Discord bot](#required-permissions-for-discord-bot)
  - [Installation](#installation)
  - [Configuring](#configuring)
  - [Music features](#music-features)
  - [Running](#running)
- [Get Started](#get-started)
  - [Chat](#chat)
    - [Chat Variables](#chat-variables)
  - [Model used](#model-used)
- [Commands](#commands)
- [FAQ](#faq)


# Jakey Bot
Jakey Bot is a multi-model AI and music bot with personality, designed to give you access to popular AI chatbots from Google Gemini, OpenAI, Anthropic, Mistral, LLaMA right within Discord! 

![Jakey Bot Banner](./assets/banner.png)

This bot primarily uses Gemini through [the Gemini API](https://ai.google.dev) as well as other models from OpenAI, Anthropic, Mistral, or use [OpenRouter](https://openrouter.ai) for unified access to some models using LiteLLM! Combined with best Python and Discord APIs to create a helpful AI assistants

## Platform availability
Jakey AI is available as Discord Bot. Other platforms is coming soon!

## Features
- Access to the top AI flagship models right within Discord!
- Summarize text channels and messages
- Multimodality support and summarize file attachments!\*
- Browse, run python code, edit images right within chat\**
- Create images using and Stable Diffusion 3.5!

Other non-AI extras include:
- Listen to music using wavelink! Play with your tunes from Spotify, SoundCloud, YouTube, and more! Right within Discord!
- Mimic other users

> \* - Gemini can take images, videos, audio, certain text files, and full PDFs as input while others only accept image inputs \
> \** - Tools are only supported through Gemini models

# Installation and setup
## Required permissions for Discord bot
- Read message history for channel summaries
- Embed messages (required for rendering text more than 2000 and for most commands)
- Send messages
- Attach files
- Create webhooks (for mimic commands)
- Create/Use slash commands
- Create and send messages in threads
- View Channels
- Add Reactions

OPTIONAL:
- Create events (for creating events using events tool)
- Connect, Speak, use Voice Activity for music features, you do not need to enable this if you don't plan to add wavelink as a dependency

For demo version, you can add this bot and see the required permissions and capabilities: https://discord.com/oauth2/authorize?client_id=1051409808877699072&permissions=563330095107136&integration_type=0&scope=bot

## Installation
The best way to get started is through Docker method... You can directly pull the image from my Docker 🐳 Hub repository and simply run the bot below:
```
~ $ docker pull zavocc/jakey:sugilite
~ $ docker run -it --env-file dev.env --rm zavocc/jakey:sugilite
```

NOTE: You need to provide [the dev.env file](#configuring) as explained below

<details>
  <summary>Manual installation</summary>
  But if you prefer manual method without using containers, you need to install Python version atleast 3.10+ with pip and venv is highly preferred and run the commands

  You must create a virtual environment before proceeding which you can do by running:
  ```
  python -m venv .venv

  # Activate
  . .venv/bin/activate
  ```

  Install dependencies as needed
  ```
  pip3 install -r requirements.txt

  # This is optional
  pip3 install wavelink gradio_client
  pip3 uninstall py-cord discord.py
  pip3 install py-cord
  ```
</details>

## Configuring
After you install the required dependencies, configure your bot first by heading over to [dev.env.template](./dev.env.template) and save it as `dev.env` in the gitroot directory

You will need to provide Discord bot token from the developers portal.

Please see [CONFIG.md](./docs/CONFIG.md) for more information about configuration.

## Music features
You can enable VC-related commands such as `/voice play` (which plays videos from YouTube and other supported sources) by providing appropriate Lavalink sources

Please see [CONFIG.md#voice](./docs/CONFIG.md#voice) to configure wavelink

You can use the list of 3rd party servers from and use servers from https://lavalink.darrennathanael.com/NoSSL/lavalink-without-ssl/ and configure the `dev.env` file pointing the third party Lavalink servers, no installation required... 

Alternatively, you can also host your own... Refer to [lavalink documentation](https://lavalink.dev/getting-started/index.html) to configure your own lavalink setup... make sure to install OpenJDK before you proceed.
## Running
After everything is configured, you can run `main.py`

# Get Started
Get started by asking Jakey `/ask prompt:Who are you and how can I get started` or **@Jakey what can you do?**

## Chat
Once you added or installed Jakey to your server or yourself, you can mention @Jakey along with your prompt or directly message Jakey in DMs. If you use Gemini model, you can prompt files such as images, audio, video, and visual PDFs too!

### Chat Variables
When you enter a prompt to Jakey... you can use chat variables which are substrings to detect which action to perform before sending the request to LLM

- `prompt /chat:ephemeral` - Do not append the last message turn to chat history while having its previous memory
- `prompt /model:model-name` - Set model for the response on demand. (See `/model list` to choose available model names)

## Model used
By default, it uses **Gemini 2.0 Flash** a workhorse model, comparable with frontier models such as GPT-4o and surpasses Gemini 1.5 Pro in most key benchmarks at a fraction of a cost. Read more [here](https://developers.googleblog.com/en/gemini-2-family-expands/)

Other AI features uses Gemini, the reason for this is the AI features of this bot started with Gemini model.

You can also sticky set the model using `/model set` command, or list models using `/model list` command. \
If you decide to use OpenRouter model, you will need to configure `/openrouter` command first by setting the model names through https://openrouter.ai/models

When you set a model, you are switching chat threads to that model associated for that provider... So switching to GPT-4o model would have its own chat thread and files, but you can always switch back to previous provider with it's memory. Note that switching models for OpenRouter would result in chat thread being cleared to ensure consistency 

If you decide to use other models please see [Models comparison](https://github.com/zavocc/JakeyBot/wiki/Supported-Models) and [the LLM arena by livebench](https://livebench.ai/) to understand your models use cases.

# Commands
Jakey provides slash commands such as:
- `/ask` - Ask Jakey quick questions.
- `/sweep` - Clear the conversation
- `/feature` - Extend Jakey skills by activating chat tools! (Clears conversation when feature are set, only supports Gemini models)
- `/model set` and `/model list` to list available models.
- `/openrouter` - Access additional models from OpenRouter (`/model set:openrouter` must be set)
- `/summarize` - Summarize the current text channel or thread and gather insights into a single summary thanks to Gemini 2.0 Flash's long context it can understand conversations even from the past decade!
- `/mimic` - Mimics other users using webhook
- `/voice` - Basic streaming audio functionality from YouTube, soundcloud and more!

Jakey also has message actions or apps which is used to take action on a selected message. Such as explain, rephrase, or suggest messages using Gemini 2.0 Flash.

![apps](./assets/apps.png)

# FAQ
Please see [FAQ](./docs/FAQ.md) for more information.