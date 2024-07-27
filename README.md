## Jakey Bot
Jakey Bot is a Gemini-based chatbot with personality, powered by Gemini 1.5 Pro and Flash

![Jakey Bot Banner](./assets/banner.png)

This chatbot is designed to utilize the [Gemini API](https://aistudio.google.com) and combine with best Python and Discord APIs to create a helpful chatbots

## UI/UX availability
Jakey AI is available as Discord Bot. Standalone UI is coming soon

## Features
- It uses the latest and greatest Gemini 1.5 models with extensive multimodal 
capabilties, this chatbot can accept text, images, video, and text files to input. With models to choose from
- Enables and exposes AI tools and features such as JSON mode, code execution, and system instructions for personality
- It can summarize messages and integrate to Discord
- Chat history per guild or user session (chat history is stored under pickle that snapshots the Gemini API chat history objects)
- Gemini API requests are asynchronous

## Installation
Core dependencies is Python with PIP, depending on your distribution, pip must be installed separately along with venv. If you want to enable music chatbot mode, you'll also need to install ffmpeg/openjdk

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
    If you use Linux distros, I strongly require you to install Python with venv support due to [PEP 0668](https://peps.python.org/pep-0668/) and [PEP 453](https://peps.python.org/pep-0453/) for rationale.

### Optional dependencies
- OpenJDK 17 with ffmpeg \
    Needed for voice commands (wavelink/lavalink)

### Installation
Once you activated your enviornment and has pip ready, you can run
```
pip3 install -r requirements.txt
```

After you installed the dependencies, don't run `main.py` just yet. You must run these commands before installing, since Wavelink installs `discord.py` as dependency and we use `py-cord` due to ease of use
```
pip3 uninstall py-cord discord.py
pip3 install py-cord
```

## Configuring
<!-- Suggested code may be subject to a license. Learn more: ~LicenseLog:3141877449. -->
After you install the required dependencies, head over to [dev.env.template](./dev.env.template) and save it as `dev.env` in the gitroot directory

Required fields to configure:
- `TOKEN` - Your Discord Bot Token
- `GOOGLE_AI_TOKEN` - Gemini API token, please see [this link](https://aistudio.google.com/app/apikey) to obtain API keys (Its free)
- `SYSTEM_USER_ID` - Its strongly advisable you to use your Discord user ID for administrative commands like eval. You probably don't want me to control your infrastructure 😉

Please see [CONFIG.md](./docs/CONFIG.md) for more information about configuration.

### Voice commands configuration:
You can enable VC-related commands such as `/voice play` (which plays videos from YouTube and other supported sources) by downloading [Lavalink jar file](https://github.com/lavalink-devs/Lavalink/releases) and placing it as `wavelink/Lavalink.jar` in project's root directory.

Activate voice by placing `Lavalink.jar` from lavalink releases and rename `application.yml.template` to `application.yml` and run `java -jar Lavalink.jar` in separate session before starting the bot.

## Running the server
After everything is configured, you can run `main.py`

Get started by asking Jakey `/ask prompt:Who are you and how can I get started`

By default, it uses **Gemini 1.5 Flash** because it's cheap, widely used, and has the same multimodal and contextual capabilities as Pro but it is statistically nerfed in terms of performance and diverse domain understanding, but it is much better than **1.0 Pro** and **GPT-3.5** and on-parity (in some cases outclasses) with the first GPT-4 model snapshot from March 2023. Please see [the LLM arena for comparison](https://arena.lmsys.org/)

## Get started
Jakey provides commands such as:
- `/ask` - Ask Jakey anything!
  - Get started by asking `/ask` `prompt:` `Hey Jakey, I'm new, tell me your commands, features, and capabilities`
  - Accepts file attachments in image, video, audio, text files, and PDFs (with images) by passing `attachment:` parameter
  - JSON mode with `json_mode:True`
  - Ephemeral conversation with `append_hist:True`
  - You can choose between **Gemini 1.5 Flash** or **Gemini 1.5 Pro** using `model:` parameter
- `/sweep` - Clear the conversation
- `/feature` - Extend Jakey skills by activating chat tools! (Clears conversation when feature are set)
- `/imagine` - Create images using Stable Diffusion 3
- `/summarize` - Summarize the current text channel or thread and gather insights into a single summary thanks to Gemini 1.5 Flash's long context it can understand conversations even from the past decade!
- `/mimic` - Mimics other users using webhook
- `/voice` - Basic streaming audio functionality from YouTube, soundcloud and more!

Jakey also has apps which is used to take action on a selected message. Such as explain, rephrase, or suggest messages.  

![apps](./assets/apps.png)

## FAQ
This is FAQ for people using this bot, please see [FAQ for technical users](./docs/FAQ.md) to understand how data is stored or how the code works under the hood.

### Why Jakey instead of standard Gemini personality?
Personality is implemented in the chatbot so to make it more human-like. However, it is based on a guy and Jakey's name is based on Jake which is mostly a masculine name (and no, don't expect Jakey to be your AI girlfriend). Prefer to keep it neutral however.

### Can it search the internet?
Not yet, but it can execute code, use files as a data source such as videos, audio, images, or text documents including PDFs with images (using OCR+Vision from Files API). (use `attachment:` parameter in `/ask` command)

You can also use [tools](./docs/TOOLS.md) using `/feature` command for Jakey to interact with services from outside world.

For now, you can attach HTML files manually and use it as a data source
![img](./assets/internet.png)

### Are models free to use?
Yes, both 1.5 Pro and Flash are free to use, and the latter is used by default (overriden by `model:` parameter) \
The only limit is rate limit. 1.5 pro rate limits are usually lowest than flash.

If you have an account with higher rate limits, we suggest to self-host this bot and use your own API keys from [AI studio](https://aistudio.google.com) with billing enabled to serve your users. Vertex AI and other non-Google AI models are not supported at this time.

### Can this bot be user-installable?
You can use `/ask`, `/imagine` and `/sweep` commands in the bot's DM once you install this app by tapping "Add app" in its profile card and clicking "Try it yourself" otherwise you will get "Integration error" when directly using these commands in DMs.

https://support.discord.com/hc/en-us/articles/23957313048343-Moderating-Apps-on-Discord#h_01HZQQQEADYVN2CM4AX4EZGKHM

Keep in mind that after installing the app to yourself, mentioned commands are exposed anywhere even if the bot is not authorized in guilds you've joined. Using `/ask` and `/sweep` commands are not supported outside DMs or guilds where the bot is authorized despite it can be visible from anywhere if its installed by user scope. This is due to because some actions like `ctx.send` will prematurely end the command with `Missing Access` error.
