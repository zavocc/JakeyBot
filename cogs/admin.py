import subprocess
from discord.ext import commands
from discord import File
from os import environ, mkdir, remove
from pathlib import Path

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Shutdown command
    @commands.command(aliases=['exit', 'stop', 'quit', 'shutdown'])
    async def admin_shutdown(self, ctx):
        """Shuts down the bot"""
        if ctx.author.id != int(environ.get("SYSTEM_USER_ID")):
            await ctx.respond("Only my master can do that >:(")
            return

        await ctx.send("Shutting down...")
        await self.bot.close()

    # Execute command
    @commands.command(aliases=['eval', 'evaluate'])
    async def admin_execute(self, ctx, *shell_command):
        """Execute a shell command inline, useful for troubleshooting or running quick maintenance task (owner only)"""
        if ctx.author.id != int(environ.get("SYSTEM_USER_ID")):
            await ctx.respond("Only my master can do that >:(")
            return

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
        if output.stdout:
            # If the output exceeds 2000 characters, send it as a file
            if len(output.stdout.decode('utf-8')) > 2000:
                # Check if temp folder exists
                if not Path("temp").exists(): mkdir("temp")

                with open("temp/output.txt", "w+") as f:
                    f.write(output.stdout.decode('utf-8'))

                await ctx.respond(f"I executed `{pretty_shell_command}` and got:", file=File("temp/output.txt", "output.txt"))

                # Delete the file
                remove("temp/output.txt")
            else:
                await ctx.respond(f"I executed `{pretty_shell_command}` and got:")
                await ctx.send(f"```{output.stdout.decode('utf-8')}```")
        else:
            await ctx.respond(f"I executed `{pretty_shell_command}` and got no output")


    # TODO: To write a better implementation of "eval" command, this code is very buggy
    # Evaluate command
    #@commands.command()
    #async def admin_evaluate(self, ctx, *python_expression):
    #    """Evaluates a python code (owner only)"""
    #    if ctx.author.id != 1039885147761283113:
    #        await ctx.respond("Only my master can do that >:(")
    #        return
    #    
    #    # Check for arguments
    #   if not python_expression or len(python_expression) == 0:
    #        await ctx.respond("You need to provide a inline python expression to evaluate")
    #        return
    #
    #    # Tuple to string as inline f-string doesn't work with these expressions
    #   pretty_py_exec = " ".join(python_expression)
    #
    #    try:
    #        output = eval(f"{pretty_py_exec}")
    #    except Exception as e:
    #        await ctx.respond(f"I executed `{pretty_py_exec}` and got an error:\n{e}")
    #        return
    #
    #   # Print the output
    #    if output is not None:
    #        # Send the output to file if it exceeds 2000 characters
    #       if len(str(output)) > 2000:
    #            # Check if temp folder exists
    #            if not Path("temp").exists(): mkdir("temp")
    #
    #            with open("temp/py_output.txt", "w+") as f:
    #                f.write(output)
    #
    #            await ctx.respond(f"I executed `{pretty_py_exec}` and got:", file=File("temp/output.txt", "output.txt"))
    #
    #            # Delete the file
    #            remove("temp/py_output.txt")
    #        else:
    #            await ctx.respond(f"I executed `{pretty_py_exec}` and got:\n```{str(output)}```")
    
def setup(bot):
    bot.add_cog(Admin(bot))
