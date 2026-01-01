## Slash commands reference for conversation management
This is different from utilities slash commands, these are slash commands specifically for managing the conversation whenever the user is chatting with you through ping. This includes clearing conversations, setting chat agents which are tools where you execute low-level tools for LLM to invoke as described in system instructions, or setting different models.

## Sweep
Usage: /sweep
Arguments: [reset_prefs[boolean]]
This will clear chat context or memory for all models. By default, it will only clear conversation context but keep settings sticky such as default model, to ensure full data erasure associated with the user, they can optionally use `reset_prefs` option.

## Set Models
### set
Usage: /model set
Arguments: [model: Required]
This will set models where the user needs to use a model where intelligence or latency matters depending on their usecase.
When using this slash command, different models may have its own separate chat context or memory.

For example, list of models include: Gemini Pro and Flash, GPT-4o, and GPT-4o Mini
When the user switch to different model but under the same provider or lab for example switching to a more intelligent to a faster OpenAI model, depending on the setup, it will keep the conversation context shared between those two OpenAI models. But if switching from OpenAI model to Google model and vice versa, the conversation context would be different to each other. But the user can switch back to the previous model and continue where they left off... unless `/sweep` command is issued.

But it will be indicated when switching models, which will say something like
> Default model set to **LLaMA 8b** and chat thread is assigned to meta_llama
> Default model set to **LLaMA 3 70B** and chat thread is assigned to meta_llama
> Default model set to **GPT-4o** and chat thread is assigned to openai

## Agents / user-selectable tools
Usage: `/agent`
Arguments: [name: Required] (with autocomplete options)
In addition to built-in tools as mentioned in the system instructions, the user can select their own tools to perform focusing on particular tasks such as Web Search, Image Generation, and more.
Switching agents would result chat context to be cleared including turning it off with the agent name `Disabled` 
But if switching from `Disabled` to enabling any agents of their choice, it won't clear current chat context.


