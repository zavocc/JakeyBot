# FAQ
### How can I make Jakey answer responses to its pure form?
You can enable or disable personality for each AI models by setting `enable_system_instruction: true` attribute to [models.yaml](../data/models.yaml)

### What is the default model used?
Default model used is determined in [models.yaml](../data/models.yaml) with first one having `default: true` will be set.

For most commands like `/summarize` or message actions, it is determined in [text_models.yaml](../data/text_models.yaml) with first one having `default: true` will be set.

### What type of files I can provide along with my prompt
Depending on AI models, most models would only accept images, Gemini models can accept images, text, PDF, and audio, and other text files.

### I get some error when using JakeyBot in DMs
You can chat with Jakey and `/sweep` commands in the bot's DM once you install this app by tapping "Add app" in its profile card and clicking "Try it yourself" otherwise you will get "Integration error" when directly using these commands in DMs.

### When I use ask command in other servers, I get an error saying "This commmand can only be used in DMs or authorized guilds!"
When you authorize your app to be usable in DMs as mentioned [above](#i-get-some-error-when-using-jakeybot-in-dms) but you cannot use it outside servers where JakeyBot isn't fully authorized

https://support.discord.com/hc/en-us/articles/23957313048343-Moderating-Apps-on-Discord#h_01HZQQQEADYVN2CM4AX4EZGKHM

The reason for this as Jakey ask command uses `ctx.send` which is not allowed with user-installable apps, which causes the command to prematurely end.

### When I switch models, GPT-4o doesn't remember what we discussed with Gemini or Anthropic model and vice versa
This is a normal behavior, your chat session gets divided per model provider. So, when you talk to OpenAI, it will have its own memory, similarly to Claude which it has its own memory.

### Will you support locally hosted or open source models soon like OLLAMA?
You can add new models in [models.yaml](../data/models.yaml) and use `litellm` as SDK to specify models.

For more information on how to add custom models, please see. [How to add new models to Jakey](./NEW_MODELS.md)

### How is my data handled?
> NOTE: The demo version of Jakey may have models that has each data handling policy. For example, free endpoints used may have data training policy that interactions will be used to train models. This includes like OpenRouter free models, Gemini API free tier, and OpenAI data sharing complementary tokens. Never provide sensitive information!

The data depends on your provided models and its respective data retention policies. Please see your respective model provider's privacy policy page to refer on how AI models used to train models