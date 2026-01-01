## Slash commands reference for utilities
These are slash commands for fun stuff or utility commands.

## Mimic command
Usage: /mimic 
Arguments: [user: Required] [message: Required]
This works as long webhooks permissions is granted, this will simply send a message appearing like other users but with [BOT] or [APP] tag next to the username as limitation
This command is only available to be used inside the server with webhook permissions.

## Avatar tools
### show
Usage: /avatar show
Arguments: [user] [describe[boolean]]
By default, it will show current user's avatar. When describe parameter is set to true, it will use an LLM to generate image descriptions.
### remix
Usage: /avatar remix
Arguments: [style: Required] [user] (with autocomplete options)
It will generate an existing user's avatar or optionally somebody else's avatar with the given style using an Image-to-Image AI model.

Both commands are available to be used both in DMs and servers

## Polls
### create
Usage: /polls create
Arguments: [prompt: Required]
Creates polls using an LLM using natural language and turns it into a discord.Poll message object, user can simply prompt to create a poll, with the ability to steer the duration and poll type (multiple/single choice).
The command will fail when trying to ask for irrelevant or contradictory request like "Do not create a poll"
Only available to be used in a server.

## Summarize
Usage: /summarize
Arguments: [steer] [before_date] [around_date] [after_date] [max_references] [limit] [model]
To summarize the current text channel messages
- steer: Additional instructions when summarizing messages
- before_date, around_date, after_date:
  These can be used altogether but it's recommended to use a valid date range from oldest to newest and the format is MM/DD/YYYY
- max_references: Number of references to include, 1-10 references.
- limit: Limit the number of messages to be included, 5-100 messages.
- model: Selects model, it includes the choice of low-latency and cost-sensitive models.
This command can only be used in a server with active text channel that's not NSFW-marked.