# Configuration

This document defines the `config.yaml` variables used to configure the Discord bot. To get started, copy `config.yaml.template` file to `config.yaml`.

## Bot

- `bot.token`: Set the Discord bot token, get one from [Discord Developer Portal](https://discord.com/developers/applications).
- `bot.name`: Set the name of your bot (defaults to "Jakey Bot")
- `bot.prefix`: Set the command prefix for the bot (defaults to "$")
- `bot.system_user_id`: Your Discord user ID for owner-only commands.
- `bot.max_context_history`: Maximum message history count.
- `bot.shared_chat_history`: Enable shared chat history for guilds.

## Database

- `database.mongodb.url`: Connection string for MongoDB database server.
- `database.mongodb.name`: Name of the database.
- `database.mongodb.collection_name`: Name of the collection within the database.

## API Keys

- `api_keys.gemini`: Gemini API token from [Google AI Studio](https://aistudio.google.com/app/apikey).
- `api_keys.openai`: OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys).
- `api_keys.anthropic`: Anthropic API key.
- `api_keys.mistral`: Mistral API key.
- `api_keys.xai`: XAI API key.
- `api_keys.groq`: Groq API key from [Groq Cloud Console](https://console.groq.com/keys).
- `api_keys.openrouter`: OpenRouter API key.
- `api_keys.moonshot_kimi`: Moonshot Kimi API key.
- `api_keys.youtube_data_v3`: YouTube Data API key. [Enable this API](https://console.cloud.google.com/apis/api/youtube.googleapis.com).
- `api_keys.exa`: Exa API Key, refer to [here](https://docs.exa.ai/websets/api/get-started).
- `api_keys.github_token`: GitHub token with public access from https://github.com/settings/personal-access-tokens.
- `api_keys.bing_subscription_key`: Bing search API key.
- `api_keys.azure_tts_key`: Azure TTS API key.
- `api_keys.fal_key`: Fal.AI API key.
- `api_keys.hf_token`: Hugging Face token.
- `api_keys.csc_gcp_api_key`: Google Cloud Custom Search API Key.

## Azure

- `azure.ai.flux_endpoint`: Azure AI Flux endpoint.
- `azure.ai.flux_key`: Azure AI Flux key.
- `azure.ai.api_base`: Azure AI API base URL.
- `azure.ai.api_key`: Azure AI API key.
- `azure.storage.account_url`: Azure blob storage URL for file uploads.
- `azure.storage.connection_string`: Azure storage connection string.
- `azure.storage.container_name`: Azure storage container name.
- `azure.tts.region`: Azure TTS region.
- `azure.subscription_id`: Azure subscription ID.
- `azure.access_token`: Azure access token.

## OpenRouter

- `openrouter.site_url`: Your site URL for OpenRouter ranking.
- `openrouter.app_name`: Your app name for OpenRouter ranking.

## Lavalink

- `lavalink.uri`: Lavalink server URI.
- `lavalink.password`: Lavalink server password.

## Chroma

- `chroma.http_host`: Chroma DB host.
- `chroma.http_port`: Chroma DB port.

## Custom Search Engine

- `cse.search_engine_cxid`: Custom Search Engine ID.

## Administrative

- `admin.temp_dir`: Path to store temporary files. Defaults to `temp/`.
