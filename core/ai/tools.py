import tools.builtin
import tools.hfspaces
import tools.websearch

# Base class for function declarations for function calling for use with built-in tools
class BaseFunctions:
    def __init__(self, bot, ctx):
        self.builtins = tools.builtin.ToolImpl(bot, ctx)
        self.hfspaces = tools.hfspaces.ToolImpl(bot, ctx)
        self.websearch = tools.websearch.ToolImpl(bot, ctx)

        # Built in
        self.artifacts = self.builtins.artifacts
        self.randomreddit = self.builtins.randomreddit
        self.youtube = self.builtins.youtube

        # HuggingFaces endpoints
        self.image_generator = self.hfspaces.image_generator

        # Web Search
        self.web_browsing = self.websearch.web_browsing
        

    # Tool methods
    async def _callable_randomreddit(self, subreddit: str):
        return await self.builtins._randomreddit(subreddit)
    
    async def _callable_youtube(self, query: str, is_youtube_link: bool):
        return await self.builtins._youtube(query, is_youtube_link)
    
    async def _callable_image_generator(self, image_description: str, width: int, height: int):
        return await self.hfspaces._image_generator(image_description, width, height)
    
    async def _callable_web_browsing(self, query: str, max_results: int = 6):
        return await self.websearch._web_browsing(query, max_results)
    
    async def _callable_artifacts(self, contents: str, filename: str):
        return await self.builtins._artifacts(contents, filename)
