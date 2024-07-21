from discord.commands import SlashCommandGroup
from discord.ext import commands
import discord
import wavelink

# For now everything is taken from https://pypi.org/project/WavelinkPycord/ but "class"ified bad pun intended
class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_user = None

    voice = SlashCommandGroup("voice", "Access voice features!", contexts={discord.InteractionContextType.guild})

    @voice.command()
    @discord.option(
        "search",
        description="Search for a query or a YouTube URL to play",
        required=True
    )
    async def play(self, ctx, search: str):
        """Play music or audio from YouTube, enter a search query or a YouTube URL to play"""

        if hasattr(ctx, "voice_client") and hasattr(ctx.author.voice, "channel"):
            if ctx.voice_client:
                vc: wavelink.Player = ctx.voice_client
                # If the bot is connected to a different channel than the user, disconnect and connect to the user's channel
                if vc.channel != ctx.author.voice.channel:
                    #if hasattr(vc, "playing") and vc.playing or hasattr(vc, "paused") and vc.paused:
                    #    await vc.stop()
                    #await vc.disconnect()
                    #vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                    # That code is buggy, has higher delay bug so for now, we prompt the user to move to another voice channel where it originally started
                    await ctx.respond("⚠️ Please move to the voice channel where the bot is currently playing.")
                    return
            else:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)   
        else:
            return await ctx.respond('🎤 Please join a voice channel.')

        # Check if there is a playback on the voice client, otherwise, clear the current user record
        if self.current_user is not None and hasattr(vc, "playing") or hasattr(vc, "paused"):
            if vc.playing or vc.paused:
                if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
                    if self.current_user != ctx.author.id:
                        return await ctx.respond('⚠️ You are not the one who queued this track.')
        else:
            self.current_user = None

        # Search for tracks using the given query and assign it to the tracks variable
        try:
            tracks = await wavelink.Playable.search(search, source=wavelink.TrackSource.YouTube)
        except discord.ext.commands.errors.MissingRequiredArgument:
            await ctx.respond('⚠️ Please specify a search query.')
            return

        # If there are no tracks found, return a message
        if not tracks:
            await ctx.respond(f'❓ No tracks found with query: `{search}`')
            return
        
        # If there are tracks found, play the first search result
        track = tracks[0]

        await vc.play(track)
        await ctx.respond(f'▶️ Playing track: **{track.title}**')

        # Temporarily save user id to check if the user is the one who queued the track
        # For moral purposes

        # Set the user currently playing the track to the class-level variable
        self.current_user = ctx.author.id

    @voice.command()
    async def status(self, ctx):
        """Get status of the currently playing track or queue"""
        vc: wavelink.Player = ctx.voice_client
    
        # Check for playback
        if not hasattr(vc, "playing") or not hasattr(vc.current, "title"):
            await ctx.respond("❌ You are not playing any tracks!")
            return

        user = await self.bot.fetch_user(self.current_user)
        avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        embed = discord.Embed(
            title='Now Playing',
            description=f'[{vc.current.title}]({vc.current.uri})',
            color=discord.Color.red()
        )

        embed.add_field(name='Playing on', value=vc.channel)
        # Player status
        if not hasattr(vc, "paused") or not vc.paused:
            embed.add_field(name='Status', value='Playing')
        else:
            embed.add_field(name='Status', value='Paused')

        # Add fields for the music author, duration, and requester
        embed.add_field(name='Author', value=vc.current.author)

        # Obtain the duration of the track and convert it to minutes and seconds
        # _ is a throwaway variable since it errors about unsupported operand types
        seconds, _ = divmod(vc.current.length, 1000)
        minutes, seconds = divmod(seconds, 60)
    
        embed.add_field(name='Duration', value=f'{minutes:02d}:{seconds:02d}')
        embed.add_field(name='URL', value=vc.current.uri)

        embed.set_footer(text=(vc.current.source if not str(vc.current.source).__contains__("Unknown") else "HTTP playback"))
        embed.set_author(name=user.name, icon_url=avatar_url)
        await ctx.respond(embed=embed)

    @voice.command()
    async def ping(self, ctx):
        """Pings the wavelink.Player server for latency"""
        vc: wavelink.Player = ctx.voice_client

        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        # Check ping
        pong = vc.ping / 1000
        await ctx.respond(f"**Pong:** {pong}")

    @voice.command(
        contexts={discord.InteractionContextType.guild},
        integration_types={discord.IntegrationType.guild_install}
    )
    async def pause(self, ctx):
        """Pause the currently playing track"""
        vc: wavelink.Player = ctx.voice_client

        # We are not rude people
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user != ctx.author.id:
                return await ctx.respond('🛑 You are not the one who queued this track.')
                
        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')
        
        # Check if we are playing a track before pausing
        if not vc.playing or vc.paused: return await ctx.respond('⏸️ There is no track currently playing.')
        
        # Pause the track
        await vc.pause(True)
        await ctx.respond(f'⏸️ Paused track: **{vc.current.title}**')

    @voice.command()
    async def resume(self, ctx):
        """Resume the currently paused track"""
        vc: wavelink.Player = ctx.voice_client

        # We are not rude people
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user != ctx.author.id:
                return await ctx.respond('You are not the one who queued this track.')

        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        if not vc.paused: return await ctx.respond('▶️ Track is currently not paused.')

        # Resume the track
        await vc.pause(False)
        await ctx.respond(f'▶️ Resumed track: **{vc.current.title}**')

    @voice.command()
    async def stop(self, ctx):
        """Stop the currently playing or paused track"""
        vc: wavelink.Player = ctx.voice_client

        # Lets not be selfish and allow the user who queued the track to stop it... Only the guild owner can stop the track in case he playing porn or something
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user != ctx.author.id:
                return await ctx.respond('🎤 You are not the one who queued this track.')

        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        # Store the title in the variable before stopping the track to notifiy the user since once it's stopped, vc.current.title will be None
        current_track_title = vc.current.title
        await vc.stop()
        await ctx.respond(f'⏹️ Stopped track: **{current_track_title}**')

    @voice.command()
    async def disconnect(self, ctx):
        """Disconnects the bot from wavelink.Player and removes from the voice channel"""
        vc: wavelink.Player = ctx.voice_client

        # Disconnect only if the user initiated the connection, server administrator or the guild owner
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user != ctx.author.id:
                return await ctx.respond('You are not the one who queued this track or has insufficent admin permissions to do this.')

        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        # Check if we are playing a track before disconnecting
        if hasattr(vc, "playing") and hasattr(vc.current, "title"):
            # Store the title in the variable before stopping the track to notifiy the user since once it's stopped, vc.current.title will be None
            current_track_title = vc.current.title

            await vc.stop()
            await ctx.send(f'⏹️ Stopped track: **{current_track_title}**')

        # Disconnect the bot from the voice channel
        await vc.disconnect()
        await ctx.respond('🔌 Disconnected.')
    
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Sorry, this feature is not supported in DMs. Please use this command inside the guild.")
        else:
            raise error

def setup(bot):
    bot.add_cog(Voice(bot))
