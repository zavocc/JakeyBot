# Configuration
## Bot
This document defines the `dev.env` variables used to configure the Discord bot. To get started, copy `dev.env.template` file to `dev.env`.

- `TOKEN` - Set the Discord bot token, get one from [Discord Developer Portal](https://discord.com/developers/applications).
- `BOT_NAME` - Set the name of your bot (defaults to "Jakey Bot")
- `BOT_PREFIX` - Set the command prefix for the bot (defaults to "$")


## Database
for chat history and other settings, this may be required.
- `MONGO_DB_URL` - Connection string for MongoDB database server (for storing chat history and other persistent data)
- `MONGO_DB_NAME` - Name of the database (defaults to `jakey_prod_db`)
- `MONGO_DB_COLLECTION_NAME` - Name of the collection within the database (defaults to `jakey_prod_db_collection`)

## Generative AI features
- `GEMINI_API_KEY` - Set the Gemini API token, get one at [Google AI Studio](https://aistudio.google.com/app/apikey). If left blank, generative features powered by Gemini will be disabled.
- `OPENAI_API_KEY` - Set the OpenAI API key, obtain one from [OpenAI Platform](https://platform.openai.com/api-keys)
- `GROQ_API_KEY` - Used to access models from Groq such as Deepseek R1 distilled and LLaMA models [Groq Cloud Console](https://console.groq.com/keys)
- `OPENROUTER_API_KEY` - Set an OpenRouter API key to access models within `/openrouter` command and when the model `openrouter` is set.

If you're using LiteLLM-based SDK models [as per models.yaml spec with `sdk: litellm` set](/models/validation.py#L18-L19), you can put more environment variables here to set additional API keys


## Generative Media
Since we use Fal.AI as our primary media provider, set an API key to activate generative features.

`FAL_KEY`

## API and Search tools
To use Exa and YouTube search, you must set the following environment variables:
- `EXA_API_KEY` - Exa API Key, refer to [here](https://docs.exa.ai/websets/api/get-started)
- `YOUTUBE_DATA_v3_API_KEY` - YouTube Data API key. [Enable this API](https://console.cloud.google.com/apis/api/youtube.googleapis.com)
- `GITHUB_TOKEN` - Get one at https://github.com/settings/personal-access-tokens with public access, used for GitHub file tool.

## Administrative
- `TEMP_DIR` - Path to store temporary uploaded/downloaded attachments for multimodal use. Defaults to `temp/` in the cuurent directory if not set. Files are always deleted on every execution regardless if its successful or not, or when the bot is restared or shutdown.
