# FAQ
### How can I make Jakey answer responses to its pure form?
To provide such experiece, Jakey has a system instruction set to refer to itself, its features, and other knowledge with human-like response vibes

Currently there's no option to change this this as system instructions are part of the context history and the instructions are cached.

### Are models free to use?
Gemini models can be used for free provided you have [an API key](https://aistudio.google.com/app/apikey) for it without billing enabled.

For other models, you will need to purchase credits either from [OpenAI](https://help.openai.com/en/articles/8264644-how-can-i-set-up-prepaid-billing) for GPT-4o models or [OpenRouter](https://openrouter.ai) for everything else, and use an API key.

### What is the default model used?
Gemini 2.5 Flash for balanced chat experiences with thinking capability, but can be changed when using `/ask` command with different providers or by stickying it via `/model set:` command.

For OpenRouter based chats, GPT-4.1 mini is the default.

For most commands like `/summarize` or message actions, Gemini 2.5 Flash Nonthinking is used.

### What type of files I can provide along with my prompt
Gemini: Images, Audio, Video, PDF
Anthropic/OpenRouter: Images, PDF

### I get some error when using JakeyBot in DMs
You can use `/ask` and `/sweep` commands in the bot's DM once you install this app by tapping "Add app" in its profile card and clicking "Try it yourself" otherwise you will get "Integration error" when directly using these commands in DMs.

### When I use ask command in other servers, I get an error saying "This commmand can only be used in DMs or authorized guilds!"
When you authorize your app to be usable in DMs as mentioned [above](#i-get-some-error-when-using-jakeybot-in-dms) but you cannot use it outside servers where JakeyBot isn't fully authorized

https://support.discord.com/hc/en-us/articles/23957313048343-Moderating-Apps-on-Discord#h_01HZQQQEADYVN2CM4AX4EZGKHM

The reason for this as Jakey ask command uses `ctx.send` which is not allowed with user-installable apps, which causes the command to prematurely end.

### When I switch models, GPT-4o doesn't remember what we discussed with Gemini or Anthropic model and vice versa
This is a normal behavior, your chat session gets divided per model provider. So, when you talk to OpenAI, it will have its own memory, similarly to Claude which it has its own memory.

### Will you support locally hosted or open source models soon like OLLAMA?
Soon, but right now it only supports flagship models that most people use and ones from OpenRouter.

### How is my data handled?
> NOTE: The invite demo version of Jakey may use free tier API key services that maybe used to train your conversations. Some models like OpenAI or Anthropic may follow different data handling regulations. In order to accomodate the demo version and cover costs, we either temporarily set API endpoints to free to some models or paid models like Azure DeepSeek may have slower performance
> TO control your data, self host your own JakeyBot with your own paid API keys.

Your data isn't used to train the models or used for specific purposes that is outside of the bot's purpose and functionality. Chat history is stored and located in MongoDB database, its recommended to add authentication to the database to ensure the privacy and safety of the users.

For files attached, it always gets deleted on our side afterwards, on startup, every command execution with or without exceptions, and on bot's shutdown. We take measures to protect your privacy.