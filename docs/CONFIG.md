# Configuration

## Overview
JakeyBot now uses YAML configuration files instead of environment variables. The configuration is stored in `config.yaml` with a template available in `config.template.yaml`.

## Getting Started

1. **Copy the template**: `cp config.template.yaml config.yaml`
2. **Edit the configuration**: Fill in your actual values in `config.yaml`
3. **Required settings**: At minimum, you need to set `bot.token` with your Discord bot token

## Configuration Structure

### Bot Settings
Located under `bot:` section:
- `token` - Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications) (**REQUIRED**)
- `name` - Name of your bot (defaults to "Jakey Bot")
- `prefix` - Command prefix for the bot (defaults to "$")

### Database Configuration
Located under `database.mongodb:` section:
- `url` - MongoDB connection string for chat history and persistent data
- `name` - Database name (defaults to `jakey_prod_db_v2`)
- `collection_name` - Collection name (defaults to `jakey_prod_db_collection_v2`)
- `shared_chat_history` - Enable shared chat history for guilds (defaults to `false`)
- `max_context_history` - Maximum message history count (defaults to `69`)

### AI Provider API Keys
Located under `ai_providers:` section with subsections for each provider:

#### Google AI (Gemini)
- `ai_providers.gemini.api_key` - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Leave empty to disable Gemini features

#### OpenAI
- `ai_providers.openai.api_key` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- Leave empty to disable OpenAI features

#### Groq
- `ai_providers.groq.api_key` - Get from [Groq Cloud Console](https://console.groq.com/keys)
- Used for Deepseek R1 distilled and LLaMA models

#### OpenRouter
- `ai_providers.openrouter.api_key` - OpenRouter API key
- `ai_providers.openrouter.site_url` - Optional ranking URL
- `ai_providers.openrouter.app_name` - Optional app name

#### Other AI Providers
- `ai_providers.anthropic.api_key` - Anthropic API key
- `ai_providers.mistral.api_key` - Mistral API key
- `ai_providers.xai.api_key` - xAI (Grok) API key
- `ai_providers.moonshot.api_key` - Moonshot (Kimi) API key

#### Azure AI Foundry
- `ai_providers.azure_ai.api_base` - Azure AI Foundry endpoint
- `ai_providers.azure_ai.api_key` - Azure AI Foundry key
- `ai_providers.azure_ai.flux.endpoint` - Azure FLUX endpoint for image generation
- `ai_providers.azure_ai.flux.key` - Azure FLUX key

### Tools and Services
Located under `tools:` and `services:` sections:

#### Search and Web APIs
- `tools.search.bing_subscription_key` - Bing search API key
- `tools.search.exa_ai_key` - Exa API Key from [Exa Documentation](https://docs.exa.ai/websets/api/get-started)
- `tools.search.google_cse_cxid` - Google Custom Search Engine CX ID
- `tools.search.google_gcp_api_key` - Google Cloud Platform API key

#### YouTube
- `tools.youtube.api_key` - YouTube Data API key from [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com)

#### GitHub
- `tools.github.token` - GitHub personal access token from [GitHub Settings](https://github.com/settings/personal-access-tokens)

#### Hugging Face
- `tools.huggingface.token` - Hugging Face API token from [Hugging Face Settings](https://huggingface.co/settings/tokens)

#### File Storage and Media
- `services.azure_storage.account_url` - Azure storage account URL
- `services.azure_storage.connection_string` - Azure storage connection string
- `services.azure_storage.container_name` - Azure storage container name
- `services.fal.key` - FAL.AI API key from [fal.ai](https://fal.ai)

#### Voice and Audio
- `services.azure_tts.region` - Azure TTS region (defaults to "eastus")
- `services.azure_tts.key` - Azure Text-to-Speech key

#### Vector Database
- `services.chroma.host` - Chroma server host (defaults to "127.0.0.1")
- `services.chroma.port` - Chroma server port (defaults to 6400)

#### Music Bot
- `services.lavalink.uri` - Lavalink server URI
- `services.lavalink.password` - Lavalink password
- `services.lavalink.identifier` - Lavalink identifier

### Administrative Settings
Located under `admin:` section:
- `system_user_id` - Discord user ID for owner-only commands (eval, shutdown, etc.)

### Azure Integration
Located under `azure:` section:
- `subscription_id` - Azure subscription ID
- `access_token` - Azure access token

### Temporary Files
- `services.temp_dir` - Directory for temporary uploaded/downloaded attachments (defaults to `/tmp/discord_jakey_tmpfiles`)
- Files are automatically deleted on every execution or when the bot restarts/shuts down

## Migration from dev.env

### Automatic Fallback
The configuration system supports both YAML and environment variables:
- YAML configuration takes precedence
- Falls back to environment variables if YAML values are not found
- This provides backward compatibility during migration

### Environment Variable Mapping
| Old Environment Variable | New YAML Path |
|-------------------------|---------------|
| `TOKEN` | `bot.token` |
| `BOT_NAME` | `bot.name` |
| `BOT_PREFIX` | `bot.prefix` |
| `MONGO_DB_URL` | `database.mongodb.url` |
| `MONGO_DB_NAME` | `database.mongodb.name` |
| `MONGO_DB_COLLECTION_NAME` | `database.mongodb.collection_name` |
| `GEMINI_API_KEY` | `ai_providers.gemini.api_key` |
| `OPENAI_API_KEY` | `ai_providers.openai.api_key` |
| `GROQ_API_KEY` | `ai_providers.groq.api_key` |
| `OPENROUTER_API_KEY` | `ai_providers.openrouter.api_key` |
| `FAL_KEY` | `services.fal.key` |
| `EXA_AI_KEY` | `tools.search.exa_ai_key` |
| `YOUTUBE_DATA_v3_API_KEY` | `tools.youtube.api_key` |
| `GITHUB_TOKEN` | `tools.github.token` |
| `TEMP_DIR` | `services.temp_dir` |
| `SYSTEM_USER_ID` | `admin.system_user_id` |

## Security Best Practices

1. **Never commit config.yaml** - Add it to your `.gitignore`
2. **Use config.template.yaml** for version control
3. **Environment variables** - For sensitive data, you can still use environment variables as fallback
4. **API key management** - Regularly rotate your API keys
5. **Access controls** - Limit bot permissions to only what's necessary

## Configuration Validation

The configuration system includes:
- **Automatic validation** - Checks for required fields like bot token
- **Fallback support** - Uses defaults when optional values are missing
- **Error reporting** - Clear error messages for missing or invalid configuration
- **Runtime reloading** - Configuration can be reloaded without restarting (advanced usage)

## Troubleshooting

### Common Issues
1. **"Please insert a valid Discord bot token"** - Check `bot.token` is set correctly
2. **"Configuration file not found"** - Ensure `config.yaml` exists in the project root
3. **"Invalid YAML"** - Validate YAML syntax in your configuration file
4. **Features not working** - Check that API keys are correctly set in the appropriate sections

### Getting Help
- Validate your YAML syntax using online YAML validators
- Check the configuration template for proper structure
- Ensure all required sections are present
- Review the migration table for proper path mapping
