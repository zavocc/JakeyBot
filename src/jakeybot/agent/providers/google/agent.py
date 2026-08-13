import google.genai


class Agent:
    # TODO: pass config from model json parameters
    # TODO: add tool pending states for this class so the agent receiver can determine when to execute tools
    def __init__(self, client: google.genai.Client):
        self.client: google.genai.Client = client

    # NOTE: THIS MAY CHANGE
    async def get_pending_tool(self):
        # If this returns none then there are no pending tools
        pass

    async def generate(self, prompt: str):
        interaction = await self.client.aio.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
            stream=False
        )

        # TODO: add checks, add tool call states to instance class variable
        return interaction.output_text  # pyright: ignore
