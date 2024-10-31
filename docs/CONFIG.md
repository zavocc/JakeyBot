# Configuration
## Bot
This document defines the `dev.env` variables used to configure the Discord bot. To get started, copy `dev.env.template` file to `dev.env`.

- `TOKEN` - Set the Discord bot token, get one from [Discord Developer Portal](https://discord.com/developers/applications).

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
- `MONGO_DB_NAME` - Name of the database to put all the data or collections inside (defaults to `prod` database name). Changing the DB name would cause the current settings and other data to be changed until you revert the name back to desired database. Its recommended to set this for prod and dev purposes.

## Generative AI features
- `GEMINI_API_KEY` - Set the Gemini API token, get one at [Google AI Studio](https://aistudio.google.com/app/apikey). If left blank, generative features powered by Gemini will be disabled.
- `OPENAI_API_KEY` - Set the OpenAI API key, obtain one from [OpenAI Platform](https://platform.openai.com/api-keys)
  - `OPENAI_API_ENDPOINT` - Sets the base URL if you use GPT-4o models outside of OpenAI platform (e.g. GitHub models marketplace or Azure AI models)
    - Setting to non-openai endpoints that doesn't have GPT-4o and GPT-4o mini would not work.
- `ANTHROPIC_API_KEY` - Set the Anthropic API keys for Claude models. Obtain one from [the console](https://console.anthropic.com/settings/keys)
- `MISTRAL_API_KEY` - Set the Mistral API keys for Mistral models. Obtain one from [La Platforme](https://console.mistral.ai/api-keys/)
- `OPENROUTER_API_KEY` - Set an OpenRouter API key if you want to use models within this platform, the models will automatically make use of this backend if none of the API keys are set.
  - This will only override OpenAI, Mistral, and Anthropic providers

## Administrative
- `TEMP_DIR` - Path to store temporary uploaded/downloaded attachments for multimodal use. Defaults to `temp/` in the cuurent directory if not set. Files are always deleted on every execution regardless if its successful or not, or when the bot is restared or shutdown.

- `MAX_CONTEXT_HISTORY` - Sets soft limit how many interactions are needed until it reaches its limit, defaults to 20. It's recommended to set within reasonable values as LLM conversation history threads are stateless and can cost exponentially as the thread tokens gets passed through without caching. Consider the hard limit of MongoDB document is 16MB.

- `SHARED_CHAT_HISTORY` - Determines whether to share the chat history to all members inside the guild. Accepts case insensitive boolean values. We recommend setting this to `false` as the bot does not have admin controls to manage chat history guild wide and conversations are treated as single dialogue. Setting to `false` makes it as if interacting the bot in DMs having their own history regardless of the setting. Keep in mind that this does not immediately delete per-guild chat history when set to `false`. Use SQLite database browser to manually manage history, refer to [HistoryManagement class](../core/ai/history.py) for more information.
