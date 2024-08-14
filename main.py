from discord.ext import bridge, commands
from dotenv import load_dotenv
from os import chdir, environ, mkdir
from pathlib import Path
from inspect import cleandoc
import datetime
import discord
import importlib
import yaml

# Go to project root directory
chdir(Path(__file__).parent.resolve())

# Load environment variables
load_dotenv("dev.env")

# Playback support
playback_support=False
try:
    wavelink = importlib.import_module("wavelink")
except ModuleNotFoundError as e:
    print(f"Playback support is disabled: {e}")
else:
    if Path("_wavelink").exists() and Path("_wavelink/Lavalink.jar").is_file() and Path("_wavelink/application.yml").is_file():
        playback_support=True

# Check if TOKEN is set
if "TOKEN" in environ and (environ.get("TOKEN") == "INSERT_DISCORD_TOKEN") and (environ.get("TOKEN") is not None) or (environ.get("TOKEN") == ""):
    print("Please insert a valid Discord bot token")
    exit(2)

# Check for system user ID else abort
# This is used for eval commands
if environ.get("SYSTEM_USER_ID") == "YOUR_DISCORD_ID" or environ.get("SYSTEM_USER_ID") is None or environ.get("SYSTEM_USER_ID") == "":
    raise Exception("Please set SYSTEM_USER_ID in dev.env")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot
bot = bridge.Bot(command_prefix=commands.when_mentioned_or("$"), intents = intents)

###############################################
# Initiate wavelink for music playback feature
###############################################
async def wavelink_setup():
    await bot.wait_until_ready()
    # https://wavelink.dev/en/latest/recipes.html
    ENV_LAVALINK_URI = environ.get("ENV_LAVALINK_URI") if environ.get("ENV_LAVALINK_URI") is not None else "http://127.0.0.1:2222"
    ENV_LAVALINK_PASS = environ.get("ENV_LAVALINK_PASS") if environ.get("ENV_LAVALINK_PASS") is not None else "youshallnotpass"
    ENV_LAVALINK_IDENTIFIER = environ.get("ENV_LAVALINK_IDENTIFIER") if environ.get("ENV_LAVALINK_IDENTIFIER") is not None else "main"

    node = wavelink.Node(
        identifier=ENV_LAVALINK_IDENTIFIER,
        uri=ENV_LAVALINK_URI,
        password=ENV_LAVALINK_PASS
    )

    await wavelink.Pool.connect(
        client=bot,
        nodes=[node]
    )

###############################################
# ON READY
###############################################
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    #https://stackoverflow.com/a/65780398 - for multiple statuses
    await bot.change_presence(activity=discord.Game("/ask me anything or $help"))

    # start wavelink setup if playback support is enabled
    if playback_support:
        await wavelink_setup()

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

###############################################
# ON GUILD JOIN
###############################################
@bot.event
async def on_member_join(member):
    if datetime.datetime.now().hour < 12:
        await member.send(
            f'Good morning **{member.mention}**! Enjoy your stay in **{member.guild.name}**!'
        )
    elif datetime.datetime.now().hour < 18:
        await member.send(
            f'Good afternoon **{member.mention}**! Enjoy your stay in **{member.guild.name}**'
        )
    else:
        await member.send(
            f'Good evening **{member.mention}**! Enjoy your stay in **{member.guild.name}**'
        )


###############################################
# ON USER MESSAGE
###############################################
@bot.event
async def on_message(message):
    # https://discord.com/channels/881207955029110855/1146373275669241958
    await bot.process_commands(message)

    if message.author == bot.user:
       return
    
    if bot.user.mentioned_in(message) and message.content == f"<@{bot.user.id}>".strip():
        await message.channel.send(cleandoc(f"""Hello <@{message.author.id}>! I am **{environ.get("BOT_NAME", "Jakey Bot!*")}** ✨
                                            I am an AI bot and I can also make your server fun and entertaining! 🎉
                                            
                                            - You can ask me anything by typing **/ask** and get started
                                            - You can access most of my useful commands with **/**slash commands or use `$help` to see the list prefixed commands I have.
                                            - You can access my apps by **tapping and holding any message** or **clicking the three-dots menu** and click **Apps** to see the list of apps I have
                                            
                                            If you have any questions, you can visit my [documentation or contact at](https://zavocc.github.io)"""))
        
with open('commands.yaml', 'r') as file:
    cog_commands = yaml.safe_load(file)
    for command in cog_commands:
        # Disable voice commands if playback support is not enabled
        if command.__contains__("voice") and not playback_support:
           continue

        try:
            bot.load_extension(f'cogs.{command}')
        except Exception as e:
            print(f"\ncogs.{command} failed to load, skipping... The following error of the cog is shown below:\n")
            print(e, end="\n\n")
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
                cleandoc(f"""**{environ.get("BOT_NAME", "Jakey Bot")}** help

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
