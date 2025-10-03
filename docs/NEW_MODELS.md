## How to add new chat models to Jakey.

The [models.yaml](../data/models.yaml) file is a spec of registered models that can be used in Jakey the Discord Bot. It can support almost all models that supports OpenAI SDK, LiteLLM for broader compatibility, and the Google Generative AI SDK (for Google models with enhanced features like file uploads). 

This file is being read for validation using [ModelProps](../models/validation.py) pydantic class as a validation layer. Thus, this is being used in places like `models.providers.sdk.completion`, `model.chat_utils`, `cogs.ai.generative_chat` and `cogs.ai.chat`

## Registering models
Adding or removing models doesn't need a restart thanks to autocomplete feature in `/model set` command.

However, there are some cases where the bot needs to be restarted when specific attribute is set. For example, when setting a new default model using `default: true` YAML mapping and setting it as priority.

### the YAML file
The `models.yaml` file consists of YAML arrays of mappings
```yaml
# There will be 2 models that will appear as options in /model set command
- model_alias: grokkygrokgrok
  model_human_name: Grok 4 Fast (High)
  model_description: SOTA-efficient fast reasoning model
  sdk: litellm
  model_id: openrouter/x-ai/grok-4-fast:free
  enable_tools: true
  enable_files: true
  enable_threads: true
  enable_system_instruction: true
  default: true
  thread_name: xai
  additional_params:
    extra_body:
      reasoning:
        enabled: true
        effort: high
    extra_headers:
      HTTP-Referer: https://github.com/zavocc/JakeyBot
      X-Title: Jakey AI - Discord Bot

- model_alias: gemma
  model_human_name: Gemma 3n
  model_description: Faster for on-device tasks
  sdk: google
  model_id: models/gemma-3n-e2b-it
  enable_tools: false
  enable_files: false
  enable_threads: true
  enable_system_instruction: false
  default: false
  thread_name: googledeepmind
```

### YAML reference
You can refer to [ModelProps](../models/validation.py) for reference of supported mappings needed to `models.yaml` file

### Required parameters
- `model_alias` - Unique identifier of the model, this value is saved on user's chat history through `core.database`, this is needed to search for the list of mappings with associated alias value and otherwise throw an error if the model mapping associated with it is not found (aka not registered)
- `model_human_name` - A human readable model, needed for `/model set`
- `model_description` - A brief description about the model, needed for `/model set`
- `model_id` - Actual model ID for it to be called for inferencing
- `sdk` - Depending on the model, select the appropriate SDK for necessary APIs to generate content and its capabilities required. Supports Gemini SDK (`google`), OpenAI SDK for OpenAI models (`openai`), or broader compatibility with LiteLLM (`litellm`).

### Optional parameters
- `additional_params` - A nested mapping of additional API parameters to be passed in the respective model APIs. This is used for setting reasoning effort, extra body and headers, and more. Depending on the SDK used, please consult to [Gemini API Reference](https://ai.google.dev/api/generate-content#method:-models.generatecontent)
  Keep in mind, some parameters will be ignored even when passed depending on the SDK, this includes:
  - `temperature`
  - `max_tokens`
  - `max_completion_tokens`
  - `max_output_tokens`
  - `system_instructions`
  - `safety_settings`
  - `tools`
- `client_name` - For OpenAI (`openai`) SDK only. Specify the client name which is an attribute name, as defined in [`core.startup`](../core/startup.py) `SubClassBotPlugServices` subclass under `start_services` method. You can use this if you have custom BaseURL set.
- `default` - A boolean value whether to set the model as default. The first array mapping with the value set to `true` will take priority and will be used as default model persistently, even with `/sweep reset_prefs:True`. To change the default model, the bot must be restarted first.
- `enable_tools` - Default is `true` - Whether to determine if the model is capable of function calling, which is needed for [Agents](../tools/) that is set by the user using `/agent` command.
- `enable_files` - Default is `true` - Whether to determine if the model accepts multimodal inputs.
- `enable_threads` - Default is `true` - Setting it false will only do a fresh one-off response generation with  no persistence, useful for testing.
- `thread_name` - Defaults to the `sdk` name if not set and also shares history across models with same SDK. If you want to set different thread name for separation while using same SDK, set this.