import tools.builtin
import tools.hfspaces
import tools.websearch

# Base class for function declarations for function calling for use with built-in tools
class BaseFunctions:
    def __init__(self, bot, ctx):
        self.builtins = tools.builtin.ToolImpl(bot, ctx)
        self.hfspaces = tools.hfspaces.ToolImpl(bot, ctx)
        self.websearch = tools.websearch.ToolImpl(bot, ctx)

        self.randomreddit = self.builtins.randomreddit
        self.youtube = self.builtins.youtube
        self.image_generator = self.hfspaces.image_generator
        self.web_browsing = self.websearch.web_browsing
        

    # Tool methods
    async def _callable_randomreddit(self, subreddit: str):
        return await self.builtins.randomreddit(subreddit)
    
    async def _callable_youtube(self, query: str, is_youtube_link: bool):
        return await self.builtins.youtube(query, is_youtube_link)
    
    async def _callable_image_generator(self, image_description: str, width: int, height: int):
        return await self.hfspaces.image_generator(image_description, width, height)
    
    async def _callable_web_browsing(self, query: str, max_results: int = 6):
        return await self.websearch.web_browsing(query, max_results)
