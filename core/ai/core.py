# Defaults
class GenAIConfigDefaults:
    def __init__(self):
        self.supported_models = {
            "Gemini 1.5 Pro (2M)":"gemini-1.5-pro-001",
            "Gemini 1.5 Flash (1M)":"gemini-1.5-flash-001",
        }

        self.generation_config = {
            "temperature": 0.5,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 8192,
        }

        self.safety_settings_config = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]

        # Default model
        self.model_config = self.supported_models["Gemini 1.5 Flash (1M)"]

# Core tools
# Disabled for now, see: https://discuss.ai.google.dev/t/is-it-possible-to-use-code-execution-with-function-calling-tools/7224
class Tools:
    @staticmethod
    def image_generator(image_description: str, width: int = 1024, height: int = 1024):
        """Generate images using natural language or description and returns the image as markdown formatted hyperlink

        Args:
         - image_description: Image description to create
         - width: width of the image (default for 1024)
         - height: height of the image (defualt for 1024)
         
         The width and height is optional, if not provided, default to 1024 pixels
         Unless the user asks for a specific width and height"""
        
        # Encode image description to URL-encoded spaces
        pretty_img_desc = image_description.replace(" ","%20")
        return f"[{image_description}](https://image.pollinations.ai/prompt/{pretty_img_desc}?width={width}&height={height}&nofeed=true"

    @staticmethod
    def random_memes(subreddit: str = "memes"):
        """Fetch memes from Reddit using meme-api.com endpoint
        
        Args:
        - subreddit: subreddit to fetch memes from
        Only possible choices: wholesomememes, memes, dankmemes, linuxmemes, programmerhumor
        """

        # Supported subreddits
        supported_subreddits = ["wholesomememes", "memes", "dankmemes", "linuxmemes", "programmerhumor"]
        if subreddit not in supported_subreddits:
            return f"Subreddit {subreddit} is not supported. Supported subreddits are: {', '.join(supported_subreddits)}"

        # Fetch memes
        memes = __import__("requests").get(f"https://meme-api.com/gimme/{subreddit}").json()
        
        # Serialize objects and get the URL, image preview and title
        meme_url = memes["postLink"]
        meme_image = memes["url"]
        meme_title = memes["title"]

        # Print meme information
        return f"[{meme_title}]({meme_image}) ([source]({meme_url}))"
