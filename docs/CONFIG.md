# Configuration
## Bot
This document defines the `dev.env` variables used to configure the Discord bot. To get started, copy `dev.env.template` file to `dev.env`.

- `TOKEN` - Set the Discord bot token, get one from [Discord Developer Portal](https://discord.com/developers/applications).
- `BOT_NAME` - Set the name of your bot (defaults to "Jakey Bot")
- `BOT_PREFIX` - Set the command prefix for the bot (defaults to "$")

## Voice
These are the default settings to connect to Lavalink v4.

You can use lavalink instances in https://lavalink.darrennathanael.com/NoSSL/lavalink-without-ssl/ to make it easier to setup and get started.

- `ENV_LAVALINK_URI` - Host where Lavalink server is running (defaults to local server URI: `http://127.0.0.1:2222`)
- `ENV_LAVALINK_PASS` - Lavalink password (change this if connecting remotely) - (defaults to "youshallnotpass")
- `ENV_LAVALINK_IDENTIFIER` - Lavalink identifier (optional, used for some servers that has it, defaults to `main`)

Please do not use this module in production unless you're serving it yourself or other remote content than YouTube. Never verify your bot with YouTube playback or you'll risk violating terms in both parties.

## Database
for chat history and other settings, this may be required.
- `MONGO_DB_URL` - Connection string for MongoDB database server (for storing chat history and other persistent data)
- `MONGO_DB_NAME` - Name of the database (defaults to `jakey_prod_db`)
- `MONGO_DB_COLLECTION_NAME` - Name of the collection within the database (defaults to `jakey_prod_db_collection`)

## Generative AI features
- `GEMINI_API_KEY` - Set the Gemini API token, get one at [Google AI Studio](https://aistudio.google.com/app/apikey). If left blank, generative features powered by Gemini will be disabled.
- `OPENAI_API_KEY` - Set the OpenAI API key, obtain one from [OpenAI Platform](https://platform.openai.com/api-keys)
  - `OPENAI_API_ENDPOINT` - Sets the base URL if you use GPT-4o models outside of OpenAI platform (e.g. GitHub models marketplace)
    - Setting to non-openai endpoints that doesn't have GPT-4o and GPT-4o mini would not work.
- `ANTHROPIC_API_KEY` - Set the Anthropic API keys for Claude models. Obtain one from [the console](https://console.anthropic.com/settings/keys)
- `MISTRAL_API_KEY` - Set the Mistral API keys for Mistral models. Obtain one from [La Platforme](https://console.mistral.ai/api-keys/)
- `XAI_API_KEY` - Used to access XAI Grok 2 models. [Get an API key from XAI console](https://console.x.ai)
- `OPENROUTER_API_KEY` - Set an OpenRouter API key to access models within `/openrouter` command and when the model `openrouter` is set.
- `HF_TOKEN` - HuggingFace inference token for accessing HuggingFace serverless-supported models

## API and Search tools
To use Google Search, Bing Search, and YouTube tools, you must set the following values:
- `CSE_SEARCH_ENGINE_CXID` - Google Custom Search Engine ID (REQUIRED) [Visit your search engines and copy your Search Engine ID](https://programmablesearchengine.google.com/controlpanel/all)
- `CSC_GCP_API_KEY` - Google Cloud Platform API key for Custom Search. [Enable this API for free](https://console.cloud.google.com/apis/library/customsearch.googleapis.com) and [Configure API keys with Custom Search APIs](https://console.cloud.google.com/apis/credentials)
- `BING_SUBSCRIPTION_KEY` - Bing Search API subscription key [Get free F1 key](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
- `YOUTUBE_DATA_v3_API_KEY` - YouTube Data API key. [Enable this API](https://console.cloud.google.com/apis/api/youtube.googleapis.com)
- `GITHUB_TOKEN` - Get one at https://github.com/settings/personal-access-tokens with public access, used for GitHub file tool.

## Administrative
- `TEMP_DIR` - Path to store temporary uploaded/downloaded attachments for multimodal use. Defaults to `temp/` in the cuurent directory if not set. Files are always deleted on every execution regardless if its successful or not, or when the bot is restared or shutdown.

- `SHARED_CHAT_HISTORY` - Determines whether to share the chat history to all members inside the guild. Accepts case insensitive boolean values. We recommend setting this to `false` as the bot does not have admin controls to manage chat history guild wide and conversations are treated as single dialogue. Setting to `false` makes it as if interacting the bot in DMs having their own history regardless of the setting. Keep in mind that this does not immediately delete per-guild chat history when set to `false`. Use SQLite database browser to manually manage history, refer to [HistoryManagement class](../core/ai/history.py) for more information.
