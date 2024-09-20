# Configuration
## Bot
This document defines the `dev.env` variables used to configure the Discord bot. To get started, copy `dev.env.template` file to `dev.env`.

- `TOKEN` - Set the Discord bot token, get one from [Discord Developer Portal](https://discord.com/developers/applications).

## Voice

These are the default settings to connect to Lavalink v4. If you're willing to use different host, port, and password, please make a copy of [wavelink/application.yml.template](./wavelink/application.yml.template) to `wavelink/application.yml` and change the settings accordingly. Please configure Lavalink's yml file if you want to use proxy, changing the server port, password and so on.

Enabling plugins other than YouTube is not recommended as its optimized for YouTube playback.

You can skip the installation step above and use servers from https://lavalink.darrennathanael.com/NoSSL/lavalink-without-ssl/

- `ENV_LAVALINK_URI` - Host where Lavalink server is running (defaults to local server URI: `http://127.0.0.1:2222`)
- `ENV_LAVALINK_PASS` - Lavalink password (change this if connecting remotely) - (defaults to "youshallnotpass")
- `ENV_LAVALINK_IDENTIFIER` - Lavalink identifier (optional, used for some servers that has it, defaults to `main`)

Please do not use this module in production unless you're serving it yourself or other remote content than YouTube. Never verify your bot with YouTube playback or you'll risk violating terms in both parties.

## Database
for chat history and other settings, this may be required.
- `MONGO_DB_URL` - Connection string for MongoDB database server (for storing chat history and other persistent data)
- `MONGO_DB_NAME` - Name of the database to put all the data or collections inside (defaults to `prod` database name). Changing the DB name would cause the current settings and other data to be changed until you revert the name back to desired database. Its recommended to set this for prod and dev purposes.

## Misc
- `GOOGLE_AI_TOKEN` - Set the Gemini API token, get one at [Google AI Studio](https://aistudio.google.com/app/apikey). If left blank, generative features will be disabled.

- `SYSTEM_USER_ID` - If you're hosting a bot, please set your Discord user ID to adminisrate the bot even if you're not the administrator of the server. With great power coems great responsibility! This is used for commands like `$admin_execute` (`$eval` as alias) to do tasks like `$eval git pull --rebase` or `$eval free -h`


- `TEMP_DIR` - Path to store temporary uploaded/downloaded attachments for multimodal use. Defaults to `temp/` in the cuurent directory if not set. Files are always deleted on every execution regardless if its successful or not, or when the bot is restared.

- `SHARED_CHAT_HISTORY` - Determines whether to share the chat history to all members inside the guild. Accepts case insensitive boolean values. We recommend setting this to `false` as the bot does not have admin controls to manage chat history guild wide and conversations are treated as single dialogue. Setting to `false` makes it as if interacting the bot in DMs having their own history regardless of the setting. Keep in mind that this does not immediately delete per-guild chat history when set to `false`. Use SQLite database browser to manually manage history, refer to [HistoryManagement class](./core/ai/history.py) for more information.

## Web Search
To efficiently use web search, a chroma server (using `chroma` command) must be running to embed webpages from the search results from being scrapped and summarized to provide relevant information to the model. And to perform embed operations asynchronously in batches to improve search performance during the web search step...

You must configure chroma server address or port where it is hosted, by default, it looks up for host `localhost` and port `6400` but you can change it depending how you ran chroma server

```
CHROMA_HTTP_HOST=127.0.0.1
CHROMA_HTTP_PORT=6400
```
If neither of these options are set, web search tool will fail.
