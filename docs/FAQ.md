# FAQ for technical users
### [1] Will you add more AI models in the future
Cheaper and better models is preferred, notably open source ones like LLAMA-3, Mixtral, or Command-R plus and commercial models like Claude 3.5 Sonnet, GPT-4o. Avoiding outdated and EOLed GPT-3.5 altogether (a year older model recieved no revisions). Expecting optimizations or distillations while providing quality and cost reduction in the future.

Gemini API is preferred because of easy access to 1.5 models for free or [cheaper with context caching](https://ai.google.dev/gemini-api/docs/caching) for extensive/repetitive token usage. While adding value such as long context windows, multimodality, code execution support.

Services can be looked out for, such as [Groq Cloud](https://groq.com/) and HuggingFace API endpoints. As soon as this bot becomes less and less dependent with Gemini through code modularization.

The only non-Gemini models are for other tools like image generation which uses HuggingFace spaces API endpoints.

### How can I be ensured that my data is safe and to comply with Discord ToS for bot developers
As a developer, it's suggested to enable billing in AI studio if you're ready to deploy this bot for production, so it adheres under [Google's Gemini API Terms](https://ai.google.dev/gemini-api/terms). Only use free plan for prototyping purposes as it serves for playground for prompts and token calculations without compromising your budget, but prompt data is sent to Google. 

When storing your chat history, the host has no direct access to your conversations, and it is not stored in plaintext/JSON. It is encoded with pickle (through JSONPickle) so it involves steps to decode every objects and read your history. The chat history is encoded as [ChatSession.history](https://ai.google.dev/api/python/google/generativeai/ChatSession) object and is pickled, then it is saved on a database file using MongoDB API but this can change as the bot grows. See below how your chat history is stored for technical users.

See [this gist](https://gist.github.com/zavocc/36b5c28072a541493c404ede164ff1c3#file-genai_lowlevel_protos-py-L39-L54) for lower-level overview of `ChatSession.history` object syntax. The history consists of [genai.protos.Content](https://ai.google.dev/api/python/google/generativeai/protos/Content)([genai.protos.Part](https://ai.google.dev/api/python/google/generativeai/protos/Part)) objects which contains the information of function calling result record, multimodal data, and user/model interaction, in order to maintain conversational consistency and context.

To keep them in persistence, a database is used which stores chat history per guild. Since MongoDB or similar does not support Python object data, it is pickled and encoded in JSON/base64 format using [JSONPickle](https://pypi.org/project/jsonpickle/) which returns `str` with JSON data inline which is then inserted into database.

For users, avoid sending your personal data to the chatbot. Basic security and privacy principle of not selling out your data to random strangers should be followed, Should the host morally follows data handling from users? Vulnerable host can make a compromise (e.g. sloppy and shady cloud hosting is used for this bot hosting).

Use `append_history:False` in `/ask` command to prevent the conversation history from being recorded. No charge when using this, privacy is respected.

Commands like `Rephrase this message`, `Summarize this message`, `Suggest a response` and `/summarize` commands does NOT retain any data to the host (not stored in chat history).

See the [HistoryManagement class](./core/ai/history.py) how the history is handled with set of methods.

#### Recommendations
Set permissions `600` to the database. Or similar where everybody access is not granted.

### Where does the uploaded files go
When you submit the file to the model (`/ask prompt:Summarize this file attachment:file.md`), the data goes in the server locally first to process and upload to [Gemini API files API](https://ai.google.dev/gemini-api/docs/prompting_with_media?lang=python). Once uploaded, it is stored within the one's associated Google cloud account project under [Generative Language API](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/) and provides free 20GB of storage per project. But files uploaded are not retrievable by any means and will automatically be deleted in 48 hours thus all the multimodal data in chat history becomes void. Locally processed data is automatically deleted asynchronously in every successful and unsuccessful execution or when the bot is restarted.

`bytesIO` serves as a volatile way to submit files, but is not used because it requires more than average desktop consumer memory to store downloaded files at once on memory especially when the command is e.g. used by 100+ users asynchonously submitting files beyond 25MB with Nitro. Instead, file is transiently stored on disk and it is expected to be deleted on any events including if `requests.exception.HTTPError` was thrown. The file is chunked and touches the disk, this is done so anybody can host their own bots without memory constraints when using multimodal capabilities.

The Generative Language API project storage stores the files in unstructured way, the only management performed is `google.generativeai.get_file()`, `google.generativeai.list_files() -> Iterable`, and `google.generativeai.delete_file()`. Ref: https://ai.google.dev/api/files. URLs returned by `get_file()` are not normally downloadable.

The organization of the files within that storage is by file naming conventions, the submitted files are renamed as:
```
JAKEY.(GUILD_ID.RANDOMINT).filename
```
`JAKEY` is the prefix filename, the `GUILD_ID` is where the files are associated within specific guild or user ID (DM) context, `RANDOMINT` are random 4-digit numbers to distinguish similar file names.

Use `delete_file()` to manually delete files from the API but this breaks all multimodal inputs.

### I've looked into the source code and the chat history is being pickled, don't you think it would be mature to use SQL/no-SQL database? Also is it insecure?
The [ChatSession.history](https://ai.google.dev/api/python/google/generativeai/ChatSession) object is being snapshotted and pickle encoded, then it is saved to a database using MongoDB.

The way how chat history is being saved is being discussed by me here: https://discuss.ai.google.dev/t/what-is-the-best-way-to-persist-chat-history-into-file

Databases like PostgreSQL combined with `jsonpickle` instead of `pickle` should allow better controls and history management combined with DB credentials would make it secure, but I have no plans to put it onto the code, atleast, once I made the code clean and maintainable and known well with SQL/database knowledge.

JSONPickle is used because it encodes python objects to base64 and yields a JSON data as string. Which is suitable for standardized database storage for chat histories that is being stored per guild/user DMs. It is the solid first choice for storing the exact `ChatSession.history` object.

If security is concern, only `ChatSession.history` is preserved. Consists of protobuf objects. And it is loaded as if the chat history is still stored on memory. If incompatibilities are suspected, chat history database can be purged or disabled at will. The only security concern is would be the object itself. Soon may change with [This PR](https://github.com/google-gemini/generative-ai-python/pull/444)

### [2] JakeyBot code looks a mess, yucky, inefficient, and disgustingly works.
Nobody is perfect, so does when writing code for the first time as a hobby :)

Instead of judging people's code bad as a whole, please provide a constructive feedback and elaborate suggestion how to improve the code, I've started writing Jakey Bot since Sept 2023 and first code looked bad, and has hardcoded values, and inefficient way of storing API keys. Now, as I push this code to public, I try my best to modularize some code to make it clean and maintainable.

PR would be awesome, please make sure it can also be maintained by me as you finished "fixing" my code.

AI can be used sparingly, but be cautious what AI model you use due to knowledge cutoff when fixing this code, AI models can barely knew newer libraries from late 2023, and its also bad at following and creating new code from the internet documentation. But, contributors who has knowledge to Python programming is always valuable, there is no point contributing if all work was done by AI.

### [3] Why not use Langchain, Ollama, Llamaindex, or other AI frameworks to power Jakey Bot to solve [1] and [2]?
Without being dependent to Gemini/PaLM API in the first place the first time I wrote Jakey. This would have been easily used. But there are more than one reason to use these
1. Those AI frameworks are quite extensive to use and comprehend, learning an API is just as learning a new programming language or a skill, and has unnecessary features and dependencies that is optimized for business-use agents. Directly using APIs or endpoints from AI provider means only using features that is needed for specific applications. Also, if not used correctly, It can get unexpected charges.
2. It may fall behind AI provider's API features and has specific dependency requirement with older versions of `google-generativeai`, for example, Gemini API provides [Code execution (function call)](https://ai.google.dev/gemini-api/docs/code-execution), [File API](https://ai.google.dev/gemini-api/docs/vision?lang=python), and [JSON mode](https://ai.google.dev/gemini-api/docs/vision?lang=python) eliminating extra prompt/code needed to have these features. [Adding Custom Langchain LLM](https://python.langchain.com/v0.1/docs/modules/model_io/llms/custom_llm/) means similar without using Langchain but adds more overhead.

Please see below for utilizing embeddings-related questions

### Look [3] can do RAG for you than writing your own RAGger and Chunker to retrieve data from external sources and potentially save money
Due to long context with Gemini 1.5, embeddings almost feels unnecessary to parse larger documents or websites, especially with Gemini 1.5 Pro having 2M context. However, embeddings can be efficient for extracting relevant points and potentially saving cost and saving computational power on server load handling tokens.

Minimal rag and embedding is performed when `web_browsing` tool is used. But does not use any LLM frameworks to coordinate the data from external sources and LLM responses. Instead, `chromadb` is used for parsing, chunking, and providing relevant data from web search pages. But it is not perfect, and the chunking method used is naive, splits characters into 300 chunks due to variability of webpage layout.
