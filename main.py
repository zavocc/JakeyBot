from core.config import config
from core.startup import SubClassBotPlugServices
from discord.ext import commands
from inspect import cleandoc
from os import chdir, mkdir
from pathlib import Path
import aiofiles.os
import aiohttp
import discord
import logging
import re
import socket
import yaml

# Go to project root directory
chdir(Path(__file__).parent.resolve())

# Logging
logging.basicConfig(format='%(levelname)s %(asctime)s [%(pathname)s:%(lineno)d - %(module)s.%(funcName)s()]: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p', 
                    level=logging.INFO)

# Check if TOKEN is set
if not config.bot_token or config.bot_token == "INSERT_DISCORD_TOKEN":
    raise Exception("Please insert a valid Discord bot token in config.yaml")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Subclass this bot
class InitBot(SubClassBotPlugServices):
    def __init__(self, *args, **kwargs):
        # Create socket instance and bind socket to 45769
        self._lock_socket_instance(45769)

        super().__init__(*args, **kwargs)

        # Prepare temporary directory
        temp_dir = config.temp_dir
        if temp_dir:
            if Path(temp_dir).exists():
                for file in Path(temp_dir).iterdir():
                    file.unlink()
            else:
                mkdir(temp_dir)
        else:
            if not Path("temp").exists():
                mkdir("temp")

        # Initialize SDK clients
        self.loop.create_task(self.start_services())
        logging.info("Services initialized successfully")

        # HTTP Client
        self.aiohttp_instance = aiohttp.ClientSession(loop=self.loop)
        logging.info("HTTP client session initialized successfully")


    def _lock_socket_instance(self, port):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind(('localhost', port))
            logging.info("Socket bound to port %s", port)
        except socket.error as e:
            logging.error("Failed to bind socket port: %s, reason: %s", port, str(e))
            raise e

    # Shutdown the bot
    async def close(self):
        # Close services
        await self.stop_services()
        logging.info("Services stopped successfully")

        # Remove temp files
        temp_dir = config.temp_dir or "temp"
        if Path(temp_dir).exists():
            for file in Path(temp_dir).iterdir():
                await aiofiles.os.remove(file)
            
        # Close socket
        self._socket.close()

        await super().close()

bot = InitBot(command_prefix=config.bot_prefix, intents = intents)

###############################################
# ON READY
###############################################
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(f"Preparing the bot for it's first use..."))
    #https://stackoverflow.com/a/65780398 - for multiple statuses
    await bot.change_presence(activity=discord.Game(f"@ me to get started!"))
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

bot.run(config.bot_token) 
