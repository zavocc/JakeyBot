## Jakey Bot
Jakey Bot is a multi-model chatbot with personality, designed to give you access to popular AI chatbots from Google, OpenAI, Anthropic, Mistral right within Discord!

![Jakey Bot Banner](./assets/banner.png)

This bot primarily uses Gemini through [the Gemini API](https://ai.google.dev) as well as other models from [OpenAI](https://openai.com), and others from [OpenRouter](https://openrouter.ai) for other AI models for unified access. Combined with best Python and Discord APIs to create a helpful AI assistants

## Platform availability
Jakey AI is available as Discord Bot. Other platforms is coming soon!

## Features
- Access to the top AI flagship models right within Discord!
- Summarize text channels and messages
- Multimodality support and summarize file attachments!\*
- Access to O1 models!\**
- Browse, run python code, edit images right within chat\***
- Create images using FLUX.1 and Stable Diffusion 3!

Other non-AI extras include:
- Listen to music using wavelink!
- Mimic other users

> \* - Gemini can take images, videos, audio, certain text files, and full PDFs as input while others only accept image inputs \
> \** - You must have an OpenRouter account and credits to use O1 models since you don't want to pay for $100 just to access it\
> \*** - Tools are only supported through Gemini models

## Installation
The only thing you'd need is Python with PIP and venv!

### Required permissions for Discord bot
- Read message history (see [#faq](#faq) for privacy implications)
- Embed messages (required for rendering text more than 4096 and for most commands)
- Send messages (obviously)
- Attach files
- Create webhooks
- Create slash commands
- Voice related features such as connect, disconnect

### Required dependencies
- Python 3.10+ with pip \
    If you use Linux distros, I strongly require you to install Python with venv support due to [PEP 0668](https://peps.python.org/pep-0668/) and [PEP 0453](https://peps.python.org/pep-0453/) for rationale.

There may be other dependencies needed for some operations such as tools. Please see [TOOLS.md](./docs/TOOLS.md) for rationale.

### Installation
Once you activated your enviornment and has pip ready, you can run
```
pip3 install -r requirements.txt
```

Wavelink isn't installed by default, you must perform these tasks to enable music VC features
```
pip3 install wavelink
pip3 uninstall py-cord discord.py
pip3 install py-cord
```

## Configuring
After you install the required dependencies, configure your bot first by heading over to [dev.env.template](./dev.env.template) and save it as `dev.env` in the gitroot directory

You will need to provide Discord bot token from the developers portal.

Please see [CONFIG.md](./docs/CONFIG.md) for more information about configuration.

### Wavelink configuration:
You can enable VC-related commands such as `/voice play` (which plays videos from YouTube and other supported sources)

Please see [CONFIG.md#voice](./docs/CONFIG.md#voice) to configure wavelink

#### Serverless lavalink
You can use the list of 3rd party servers from and use servers from https://lavalink.darrennathanael.com/NoSSL/lavalink-without-ssl/ and configure the `dev.env` file pointing the third party Lavalink servers, no installation required... 

---

#### Your own lavalink server
You can also host your own lavalink server, you must install OpenJDK and download the [Lavalink jar file](https://github.com/lavalink-devs/Lavalink/releases) and placing it as `_wavelink/Lavalink.jar` in project's root directory.

Activate voice by placing `Lavalink.jar` and copy `application.yml.template` to `application.yml` and run `java -jar Lavalink.jar` in separate session before starting the bot.

If you decide to configure the port, address, and password, make sure it reflects to the `dev.env` file as well.


## Running the server
After everything is configured, you can run `main.py`

Get started by asking Jakey `/ask prompt:Who are you and how can I get started`

By default, it uses **Gemini 1.5 Flash** due to versatility with long context and multimodality, matching the performance of, but other models can be used as well. Jakey also supports Gemini 1.5 Pro, GPT-4o and its mini variant, o1-preview and o1-mini, and Claude 3.5 sonnet and 3 Haiku

If you decide to use other models please see [Models comparison](https://github.com/zavocc/JakeyBot/wiki/Supported-Models) and [the LLM arena by livebench](https://livebench.ai/) to understand your models use cases

## Get started
Jakey provides commands such as:
- `/ask` - Ask Jakey anything!
  - Get started by asking `/ask` `prompt:` `Hey Jakey, I'm new, tell me your commands, features, and capabilities`
  - Use multimodal features by passing `attachment:` parameter
  - Ephemeral conversation with `append_hist:True`
  - Show logs, conversation and model info with `verbose_logs:True`
  - You can choose between models using `model:` parameter
- `/sweep` - Clear the conversation
- `/feature` - Extend Jakey skills by activating chat tools! (Clears conversation when feature are set, only supports Gemini models)
- `/imagine` - Create images using Stable Diffusion 3
- `/summarize` - Summarize the current text channel or thread and gather insights into a single summary thanks to Gemini 1.5 Flash's long context it can understand conversations even from the past decade!
- `/mimic` - Mimics other users using webhook
- `/voice` - Basic streaming audio functionality from YouTube, soundcloud and more!

Jakey also has message actions or apps which is used to take action on a selected message. Such as explain, rephrase, or suggest messages using Gemini 1.5 Flash.

![apps](./assets/apps.png)

## FAQ
Please see [FAQ](./docs/FAQ.md) for more information.