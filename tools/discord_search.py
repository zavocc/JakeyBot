# Built in Tools
import google.generativeai as genai
import asyncio
import datetime
import importlib
import inspect

# Function implementations
class Tool:
    tool_human_name = "Discord"
    tool_name = "discord_search"
    tool_config = "AUTO"
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        # Random Reddit
        self.tool_schema = genai.protos.Tool(
            function_declarations=[
                genai.protos.FunctionDeclaration(
                    name = self.tool_name,
                    description = "Search and reason across text messages within the current text channel in Discord",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            'query':genai.protos.Schema(type=genai.protos.Type.STRING),
                            'max_results':genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            'around_date':genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={
                                'month':genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                'day':genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                'year':genai.protos.Schema(type=genai.protos.Type.INTEGER)
                            }, required=['month', 'day', 'year'])
                        },
                    )
                )
            ]
        )

    async def __get_embedding(self, text: str):
        _embd = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=text,
            task_type="semantic_similarity",
        )
        
        return _embd["embedding"]

    async def _tool_function(self, query: str = None, max_results: int = 50, around_date = None):
        if max_results > 100:
            max_results = 100

        try:
            numpy = importlib.import_module("numpy")
        except ModuleNotFoundError:
            return "This tool is not available at the moment"
        
        _msg_status = await self.ctx.send("🔍 Searching for messages for information...")

        # Assemble around date argument
        # From dict from openapi spec to datetime string
        _around_date = None
        if around_date:
            month = around_date["month"]
            day = around_date["day"]
            year = around_date["year"]
                    
            if month and day and year:
                _around_date = f"{int(month):02}/{int(day):02}/{int(year):04}"
        
        # Search for channels
        _results = []
        async for message in self.ctx.channel.history(limit=int(max_results), around=datetime.datetime.strptime(_around_date, "%m/%d/%Y") if _around_date else None):
            # Determine cosine similarity
            if message.content == "":
                continue

            if query:
                _query_embedding = await self.__get_embedding(text=query)
                _message_embedding = await self.__get_embedding(text=message.content)

                # Get the semantic similarity score
                _score = numpy.dot(_query_embedding, _message_embedding) / (numpy.linalg.norm(_query_embedding) * numpy.linalg.norm(_message_embedding))
            else:
                # Always score to 100
                _score = 1.0

            print(f"Score: {_score}")
            if _score >= 0.41:
                _results.append(inspect.cleandoc(f"""
                                -------------------------
                                Message by {message.author} at {message.created_at}
                                -------------------------
                                {message.content}
                                -------------------------
                                Jump link: {message.jump_url}
                                -------------------------
                                """))
            
        await _msg_status.delete()
        print(_results)
        return "Here are the messages I searched:\n{}".format("\n".join(_results)) if _results else "No results found"