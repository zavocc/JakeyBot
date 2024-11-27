import aiofiles
import aiofiles.os
import discord
import random
import subprocess
from discord.ext import commands
from os import environ

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    # Shutdown command
    @commands.command(aliases=['exit', 'stop', 'quit', 'shutdown'])
    @commands.is_owner()
    async def admin_shutdown(self, ctx):
        """Shuts down the bot"""
        await ctx.send("Shutting down...")
        await self.bot.close()

    # Execute command
    @commands.command(aliases=['eval', 'evaluate'])
    @commands.is_owner()
    async def admin_execute(self, ctx, *shell_command):
        """Execute a shell command inline, useful for troubleshooting or running quick maintenance task (owner only)"""
        # Check for arguments
        if not shell_command or len(shell_command) == 0:
            await ctx.respond("You need to provide a shell command to execute")
            return

        # Used to echo the command ran to the bot, as it errors? when this is directly used in f-string
        pretty_shell_command = " ".join(shell_command)

        # For now, shell output is disabled as it is having trouble with parsing "/" character as arguments, thus this is a security risk
        # For PIPING, we just typically use $execute bash -c "command | pipe"
        output = None
        try:
            output = subprocess.run(shell_command, shell = False,capture_output = True)
        except FileNotFoundError:
            await ctx.respond(f"Cannot execute `{pretty_shell_command}`, no such file or directory.")
        
        # Check if we should send the output to file 
        _xfilepath = f"{environ.get('TEMP_DIR')}/output{random.randint(3928,10029)}.txt"
        if output.stdout:
            # If the output exceeds 2000 characters, send it as a file
            if len(output.stdout.decode('utf-8')) > 2000:
                async with aiofiles.open(_xfilepath, "w+") as f:
                    await f.write(output.stdout.decode('utf-8'))

                await ctx.respond(f"I executed `{pretty_shell_command}` and got:", file=discord.File(_xfilepath, "output.txt"))

                # Delete the file
                await aiofiles.os.remove(_xfilepath)
            else:
                await ctx.respond(f"I executed `{pretty_shell_command}` and got:")
                await ctx.send(f"```{output.stdout.decode('utf-8')}```")
        else:
            await ctx.respond(f"I executed `{pretty_shell_command}` and got no output")

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            await ctx.respond("❌ Sorry, only the owner can use this command.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(f"❌ You are missing the required permissions to use this command. Needed permissions:\n```{error}```")
        else:
            raise error

def setup(bot):
    bot.add_cog(Admin(bot))
