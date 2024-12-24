# FAQ
### How can I make Jakey answer responses to its pure form?
To provide such experiece, Jakey has a system instruction set to refer to itself, its features, and other knowledge with human-like response vibes

Currently there's no option to change this this as system instructions are part of the context history and the instructions are cached.

### What model should I choose?
Its recommended to use Gemini 2.0 model to benefit from full multimodality, tools, and fraction of a price.

### Are models free to use?
Gemini models can be used for free provided you have [an API key](https://aistudio.google.com/app/apikey) for it without billing enabled.

For other models, you will need to purchase credits either from [OpenAI](https://help.openai.com/en/articles/8264644-how-can-i-set-up-prepaid-billing) for GPT-4o models or [OpenRouter](https://openrouter.ai) for everything else, and use an API key.

### What is the default model used?
Gemini 1.5 Flash is the default model due to low cost and versatility, but can be changed when using `/ask` command with different providers or by stickying it via `/model set:` command.

For OpenRouter based chats, GPT-4o mini is the default.

For most commands like `/summarize` or message actions, Gemini 1.5 Flash is used.

### What type of files I can provide along with my prompt
Not all models are inherently multimodal and capabilities.

Gemini models benefits from full multimodality, you can provide files like images, videos, audio, text files like source files, and PDFs with its non-textual data retained... and only lasts within the context for 48 hours

OpenAI, XAI Grok, Mistral and Claude models can only accept images at this time.

### I get some error when using JakeyBot in DMs
You can use `/ask` and `/sweep` commands in the bot's DM once you install this app by tapping "Add app" in its profile card and clicking "Try it yourself" otherwise you will get "Integration error" when directly using these commands in DMs.

### When I use ask command in other servers, I get an error saying "This commmand can only be used in DMs or authorized guilds!"
When you authorize your app to be usable in DMs as mentioned [above](#i-get-some-error-when-using-jakeybot-in-dms) but you cannot use it outside servers where JakeyBot isn't fully authorized

https://support.discord.com/hc/en-us/articles/23957313048343-Moderating-Apps-on-Discord#h_01HZQQQEADYVN2CM4AX4EZGKHM

The reason for this as Jakey ask command uses `ctx.send` which is not allowed with user-installable apps, which causes the command to prematurely end.

### When I switch models, GPT-4o doesn't remember what we discussed with Gemini model and vice versa
This is a normal behavior, your chat session gets divided per model provider. So, when you talk to Gemini, it will have its own memory, similarly to Claude which it has its own memory.

### Will you support locally hosted or open source models soon like OLLAMA?
Soon, but right now it only supports flagship models that most people use and ones from OpenRouter.

### How is my data handled?
Your data isn't used to train the models or used for specific purposes that is outside of the bot's purpose and functionality. Chat history is stored and located in MongoDB database, its recommended to add authentication to the database to ensure the privacy and safety of the users.

For files attached, it always gets deleted on our side afterwards, on startup, every command execution with or without exceptions, and on bot's shutdown. We take measures to protect your privacy.