from discord.ext import bridge, commands
from google import genai
from inspect import cleandoc
from os import chdir, mkdir, environ
from pathlib import Path
import aiohttp
import aiofiles.os
import discord
import dotenv
import importlib
import logging
import re
import yaml

# Go to project root directory
chdir(Path(__file__).parent.resolve())

# Load environment variables
dotenv.load_dotenv("dev.env")

# Logging
logging.basicConfig(format='%(levelname)s %(asctime)s [%(filename)s:%(lineno)d - %(funcName)s()]: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p', 
                    level=logging.INFO)

# Check if TOKEN is set
if "TOKEN" in environ and (environ.get("TOKEN") == "INSERT_DISCORD_TOKEN") or (environ.get("TOKEN") is None) or (environ.get("TOKEN") == ""):
    raise Exception("Please insert a valid Discord bot token")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Subclass this bot
class InitBot(bridge.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prepare temporary directory
        if environ.get("TEMP_DIR") is not None:
            if Path(environ.get("TEMP_DIR")).exists():
                for file in Path(environ.get("TEMP_DIR", "temp")).iterdir():
                    file.unlink()
            else:
                mkdir(environ.get("TEMP_DIR"))
        else:
            environ["TEMP_DIR"] = "temp"
            mkdir(environ.get("TEMP_DIR"))

        # Wavelink
        self._wavelink = None
        try:
            self._wavelink = importlib.import_module("wavelink")
        except ModuleNotFoundError as e:
            logging.warning("Playback support is disabled: %s", e)
            self._wavelink = None

        # Gemini API Client
        self._gemini_api_client = genai.Client(api_key=environ.get("GEMINI_API_KEY"))

        # Everything else (mostly GET requests)
        self._aiohttp_main_client_session = aiohttp.ClientSession(loop=self.loop)

    # Shutdown the bot
    async def close(self):
        # Close aiohttp client sessions
        await self._aiohttp_main_client_session.close()

        # Remove temp files
        if Path(environ.get("TEMP_DIR", "temp")).exists():
            for file in Path(environ.get("TEMP_DIR", "temp")).iterdir():
                await aiofiles.os.remove(file)

        await super().close()

bot = InitBot(command_prefix=environ.get("BOT_PREFIX", "$"), intents = intents)

###############################################
# ON READY
###############################################
@bot.event
async def on_ready():
    # start wavelink setup if playback support is enabled
    if bot._wavelink is not None:
        try:
            # https://wavelink.dev/en/latest/recipes.html
            ENV_LAVALINK_URI = environ.get("ENV_LAVALINK_URI") if environ.get("ENV_LAVALINK_URI") is not None else "http://127.0.0.1:2222"
            ENV_LAVALINK_PASS = environ.get("ENV_LAVALINK_PASS") if environ.get("ENV_LAVALINK_PASS") is not None else "youshallnotpass"
            ENV_LAVALINK_IDENTIFIER = environ.get("ENV_LAVALINK_IDENTIFIER") if environ.get("ENV_LAVALINK_IDENTIFIER") is not None else "main"

            node = bot._wavelink.Node(
                identifier=ENV_LAVALINK_IDENTIFIER,
                uri=ENV_LAVALINK_URI,
                password=ENV_LAVALINK_PASS,
                retries=0 # Only connect once to save time
            )

            await bot._wavelink.Pool.connect(
                client=bot,
                nodes=[node]
            )
        except Exception as e:
            logging.error("Failed to setup wavelink: %s... Disabling playback support", e)
            bot._wavelink = None

    #https://stackoverflow.com/a/65780398 - for multiple statuses
    await bot.change_presence(activity=discord.Game(f"/ask me anything or {bot.command_prefix}help"))
    logging.info("%s is ready and online!", bot.user)

###############################################
# ON USER MESSAGE
###############################################
@bot.event
async def on_message(message: discord.Message):
    # https://discord.com/channels/881207955029110855/1146373275669241958
    await bot.process_commands(message)

    if message.author == bot.user:
       return
    
    # Check if the bot was only mentioned without any content or image attachments
    # On generative ask command, the same logic is used but it will just invoke return and the bot will respond with this
    if bot.user.mentioned_in(message) \
        and not message.attachments \
        and not re.sub(f"<@{bot.user.id}>", '', message.content).strip():
        await message.channel.send(
            cleandoc(f"""Hello <@{message.author.id}>! I am **{bot.user.name}** ✨
                    I am an AI bot and I can also make your server fun and entertaining! 🎉

                    You just pinged me, but what can I do for you? 🤔
                    
                    - You can ask me anything by typing **/ask** and get started or by mentioning me again but with a message
                    - You can access most of my useful commands with **/**slash commands or use `{bot.command_prefix}help` to see the list prefixed commands I have.
                    - You can access my apps by **tapping and holding any message** or **clicking the three-dots menu** and click **Apps** to see the list of apps I have
                    
                    You can ask me questions, such as:
                    - **@{bot.user.name}** How many R's in the word strawberry?  
                    - **/ask** `prompt:`Can you tell me a joke?  
                    - Hey **@{bot.user.name}** can you give me quotes for today?  

                    If you have any questions, you can visit my [documentation or contact me here](https://zavocc.github.io)"""))


with open('commands.yaml', 'r') as file:
    cog_commands = yaml.safe_load(file)
    for command in cog_commands:
        # Disable voice commands if playback support is not enabled
        if "voice" in command and not bot._wavelink:
           logging.warning("Skipping %s... Playback support is disabled", command)
           continue

        try:
            bot.load_extension(f'cogs.{command}')
        except Exception as e:
            logging.error("cogs.%s failed to load, skipping... The following error of the cog: %s", command, e)
            continue

# Initialize custom help
class CustomHelp(commands.MinimalHelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = "Misc"
    
    # Override "get_opening_note" with custom implementation
    def get_opening_note(self):
            """Returns help command's opening note. This is mainly useful to override for i18n purposes.

            The default implementation returns ::

                Use `{prefix}{command_name} [command]` for more info on a command.
                You can also use `{prefix}{command_name} [category]` for more info on a category.

            Returns
            -------
            :class:`str`
                The help command opening note.
            """
            command_name = self.invoked_with
            return (
                cleandoc(f"""**{bot.user.name}** help

                Welcome! here are the prefix commands that you can use!
                
                You can access my slash commands by just typing **/** and find the commands that is associated to me.
                Slash commands are self documented, I will be constantly updated to update my slash command documentation

                Use `{self.context.clean_prefix}{command_name} [command]` for more info on a command.

                You can also use `{self.context.clean_prefix}{command_name} [category]` for more info on a category.""")
            )

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=discord.Color.random())
            await destination.send(embed=embed)

bot.help_command = CustomHelp()

bot.run(environ.get('TOKEN')) 
