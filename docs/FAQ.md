# FAQ
### How can I make Jakey answer responses to its pure form?
To provide such experiece, Jakey has a system instruction set to refer to itself, its features, and other knowledge with human-like response vibes

Currently there's no option to change this this as system instructions are part of the context history and the instructions are cached.

### What model should I choose?
Its recommended to use Gemini 1.5 model to benefit from full multimodality, web search, tools, and fraction of a price.

### Are models free to use?
Gemini models can be used for free provided you have [an API key](https://aistudio.google.com/app/apikey) for it without billing enabled.

For other models, you will need to purchase credits either from [OpenAI](https://help.openai.com/en/articles/8264644-how-can-i-set-up-prepaid-billing) for GPT-4o models or [OpenRouter](https://openrouter.ai) for everything else, and use an API key.

### What is the default model used?
Gemini 1.5 Flash is the default model due to low cost and versatility, but can be changed when using `/ask` command with different providers

For most commands like `/summarize` or message actions, Gemini 1.5 Flash is used.

### What type of files I can provide along with my prompt
Not all models are inherently multimodal and capabilities.

Gemini 1.5 models benefits from full multimodality, you can provide files like images, videos, audio, text files like source files, and PDFs with its non-textual data retained... and only lasts within the context for 48 hours

OpenAI and Claude models can only accept images at this time.

### Can it search the internet?
> *This feature is currently only supports Gemini models*

Web Search (beta) can be used by enabling it under `/feature` command capability named "Web Search with DuckDuckGo" and ask queries with keywords like "Search the web"

Web search performs in two steps
1. It searches the query through DuckDuckGo API and collects the links needed for page summarization
2. The list of URLs is then being scrapped and agregates them so the model can understand them

Keep in mind that web search is slow.

The maximum number of queries can be used is 6 to prevent tokens from depleting so quickly due to large articles and causing slower responses as context builds up and performs batch chunks of webpage scrapping its contents before the response get sent from the model.

Its recommended to use Gemini 1.5 Pro to better utilize Tool use but Flash also works. Keep in mind that the model sometimes cannot pick up the tool schema needed to perform web search action, if it fabricates its responses, explicitly tell the model to search the web, or improve your prompt.

Using web search can affect the response overall performance as chat history grows, however the webpages are embedded, chunked, and stores the embeddings through temporary vector database to efficiently provide and extract relevant context to the model from the large batch of chunked corpuses of webpage contents. By default, its using its default text transformer model to embed texts locally. Its recommended to use web search sparingly if you want the model to be aware with certain information. You can also tell the model how many searches it can perform (but queries are maximum to 6) optimally 2-3 searches.

Depending on a website, some pages may not be used for responses that does not have extractable textual data.

You can also attach HTML files manually as part of attachment if you want a single page summarization
![img](../assets/internet.png)

### I get some error when using JakeyBot in DMs
You can use `/ask`, `/imagine` and `/sweep` commands in the bot's DM once you install this app by tapping "Add app" in its profile card and clicking "Try it yourself" otherwise you will get "Integration error" when directly using these commands in DMs.

### When I use ask command in other servers, I get an error saying "This commmand can only be used in DMs or authorized guilds!"
When you authorize your app to be usable in DMs as mentioned [above](#i-get-some-error-when-using-jakeybot-in-dms) but you cannot use it outside servers where JakeyBot isn't fully authorized

https://support.discord.com/hc/en-us/articles/23957313048343-Moderating-Apps-on-Discord#h_01HZQQQEADYVN2CM4AX4EZGKHM

The reason for this as Jakey ask command uses `ctx.send` which is not allowed with user-installable apps, which causes the command to prematurely end.

### When I switch models, GPT-4o doesn't remember what we discussed with Gemini model and vice versa
This is a normal behavior, your chat session gets divided per model provider. So, when you talk to Gemini, it will have its own memory, similarly to Claude which it has its own memory.

### Will you support locally hosted or open source models soon like OLLAMA?
Soon, but right now it only supports flagship models that most people use.

### How is my data handled?
Your data isn't used to train the models or used for specific purposes that is outside of the bot's purpose and functionality. Chat history is stored and located in MongoDB database, its recommended to add authentication to the database to ensure the privacy and safety of the users.

For files attached, it always gets deleted on our side afterwards, on startup, every command execution with or without exceptions, and on bot's shutdown. We take measures to protect your privacy.