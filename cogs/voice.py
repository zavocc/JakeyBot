from discord.commands import SlashCommandGroup
from discord.ext import commands
import asyncio
import discord
import typing
import wavelink

# For now everything is taken from https://pypi.org/project/WavelinkPycord/ but "class"ified bad pun intended
class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_user = {}
        self.enqueued_tracks = {}
        self.pendings = {}

    voice = SlashCommandGroup("voice", "Access voice features!", contexts={discord.InteractionContextType.guild})

    @voice.command()
    @discord.option(
        "search",
        description="Search for a query or a YouTube URL to play",
        required=True
    )
    async def play(self, ctx, search: str):
        """Play music or audio from YouTube, enter a search query or a YouTube URL to play"""
        await ctx.response.defer()
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        try:
            if not vc:
                vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        except AttributeError:
            return await ctx.respond("🎙️ You must be in a voice channel to use this command.")

        # Check if there is a playback on the voice client, otherwise, clear the current user record
        #if self.current_user.get(ctx.guild.id) is not None and hasattr(vc, "playing") or hasattr(vc, "paused"):
        #    if vc.playing or vc.paused:
        #        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
        #            if self.current_user.get(ctx.guild.id) != ctx.author.id:
        #                return await ctx.respond('⚠️ You are not the one who queued this track.')
        #else:
        #    self.current_user.update({ctx.guild.id: None})

        if ctx.author.voice.channel.id != vc.channel.id:
            return await ctx.respond("🎙️ You must be in the same voice channel as the bot.")

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

        # Initialize the enqueued tracks list
        if not self.enqueued_tracks.get(ctx.guild.id):
            self.enqueued_tracks.update({ctx.guild.id: []})

        self.enqueued_tracks.get(ctx.guild.id).append({ctx.author.id: track})
        await ctx.respond(f'➕ Added to tracks: **{track.title}**')

        if not vc.playing:
            while self.enqueued_tracks.get(ctx.guild.id):
                # Check if there is a pending shutdown state which is initiated at disconnect command
                if self.pendings.get(ctx.guild.id) == "disconnecting":
                    break

                # Use two separate variables since popping the list will remove the first element and will cause errors
                _now_playingby = self.enqueued_tracks.get(ctx.guild.id).pop(0)
                _track = _now_playingby.get(list(_now_playingby)[0])

                await ctx.send(f'▶️ Now playing track: **{_track.title}**')
                await vc.play(_track)

                # Temporarily save user id to check if the user is the one who queued the track
                # For moral purposes

                # Set the user currently playing the track to the class-level variable
                self.current_user.update({ctx.guild.id: list(_now_playingby)[0]})

                while vc.playing:
                    await asyncio.sleep(1)
        else:
            await ctx.respond(f'⌛ Waiting for the current track to finish playing...', ephemeral=True)

    @voice.command()
    @discord.option(
        "show_tracks",
        description="Show the tracks in the queue",
    )
    async def status(self, ctx, show_tracks: bool = False):
        """Get status of the currently playing track or queue"""
        # defer since the more iterations, it will cause unknown interaction error
        await ctx.response.defer()

        vc = typing.cast(wavelink.Player, ctx.voice_client)
    
        # Check for playback
        if not vc and not hasattr(vc, "playing") or not hasattr(vc.current, "title"):
            await ctx.respond("❌ You are not playing any tracks!")
            return

        user = await self.bot.fetch_user(self.current_user.get(ctx.guild.id))
        avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        _status_embed = discord.Embed(
            title='Now Playing',
            description=f'[{vc.current.title}]({vc.current.uri})',
            color=discord.Color.red()
        )

        _status_embed.add_field(name='Playing on', value=vc.channel)
        # Player status
        if not hasattr(vc, "paused") or not vc.paused:
            _status_embed.add_field(name='Status', value='Playing')
        else:
            _status_embed.add_field(name='Status', value='Paused')

        # Add fields for the music author, duration, and requester
        _status_embed.add_field(name='Author', value=vc.current.author)

        # Obtain the duration of the track and convert it to minutes and seconds
        # _ is a throwaway variable since it errors about unsupported operand types
        seconds, _ = divmod(vc.current.length, 1000)
        minutes, seconds = divmod(seconds, 60)
    
        _status_embed.add_field(name='Duration', value=f'{minutes:02d}:{seconds:02d}')
        _status_embed.add_field(name='URL', value=vc.current.uri)

        _status_embed.set_footer(text=(vc.current.source if not str(vc.current.source).__contains__("Unknown") else "HTTP playback"))
        _status_embed.set_author(name=user.name, icon_url=avatar_url)

        if not show_tracks:
            await ctx.respond(embed=_status_embed)
        else:
            await ctx.send(embed=_status_embed)

            # Iterate through the enqueued tracks list and display the tracks
            _queue_embed = discord.Embed(
                title='Enqueued Tracks',
                color=discord.Color.random()
            )

            # We use list(track)[0] as it yields keys of the dictionary (casted to list) and we can get the user id
            for track in self.enqueued_tracks.get(ctx.guild.id):
                _queue_embed.add_field(name=track.get(list(track)[0]).title, value=f'{await self.bot.fetch_user(list(track)[0])}', inline=False)

            await ctx.respond(embed=_queue_embed)

    @voice.command()
    @discord.option(
        "skip_all",
        description="Skip all the tracks created by you in the queue",
    )
    async def skip(self, ctx, skip_all: bool = False):
        """Skip the pending queue track (by you)"""
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # Check if there's even a voice client connected
        if not vc and not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        # Check if enqueue tracks list is empty
        if not self.enqueued_tracks.get(ctx.guild.id) or len(self.enqueued_tracks.get(ctx.guild.id)) == 0:
            return await ctx.respond('0️⃣ No tracks in the queue.')
        
        # Indicator where there is a skipped track
        _tracks_skipped = False

        # Check and iterate through the enqueued tracks list by the user, copy the list prevent direct reference and remove
        for track in self.enqueued_tracks.get(ctx.guild.id).copy():
            if list(track)[0] == ctx.author.id:
                # Pop the track from the list
                self.enqueued_tracks.get(ctx.guild.id).remove(track)

                if not skip_all:
                    await ctx.respond(f'⏭️ Skipped track: **{track.get(list(track)[0]).title}**')
                
                _tracks_skipped = True

                if not skip_all:
                    break
        
        if not _tracks_skipped:
            return await ctx.respond('🎵 You have no tracks in the queue.')

        # If the user skipped all the tracks
        if skip_all:
            await ctx.respond('⏭️ Skipped all the tracks created by you in the queue.')

    @voice.command()
    async def ping(self, ctx):
        """Pings the wavelink.Player server for latency"""
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # Check if there's even a voice client connected
        if not vc and not hasattr(vc, "connected"):
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
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # We are not rude people
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user.get(ctx.guild.id) != ctx.author.id:
                return await ctx.respond('🛑 You are not the one who queued this track.')
                
        # Check if there's even a voice client connected
        if not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')
        
        # Check if we are playing a track before pausing
        if not vc.playing or vc.paused: 
            return await ctx.respond('⏸️ There is no track currently playing.')
        
        # Pause the track
        await vc.pause(True)
        await ctx.respond(f'⏸️ Paused track: **{vc.current.title}**')

    @voice.command()
    async def resume(self, ctx):
        """Resume the currently paused track"""
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # We are not rude people
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user.get(ctx.guild.id) != ctx.author.id:
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
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # Lets not be selfish and allow the user who queued the track to stop it... Only the guild owner can stop the track in case he playing porn or something
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user.get(ctx.guild.id) != ctx.author.id:
                return await ctx.respond('🎤 You are not the one who queued this track.')

        # Check if there's even a voice client connected nbm
        if not vc and not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')
        
        # Check if there is a playing track or else return a message
        if not vc.playing:
            return await ctx.respond('ℹ️ There is no track currently playing.')

        # If there is a paused track, we need to resume it first before stopping it so it doesn't pause the next track
        if vc.paused:
            await vc.pause(False)

        # Store the title in the variable before stopping the track to notifiy the user since once it's stopped, vc.current.title will be None
        _current_track_title = vc.current.title
        await vc.stop()
        await ctx.respond(f'⏹️ Stopped track: **{_current_track_title}**')

    @voice.command()
    @commands.has_guild_permissions(move_members=True)
    async def disconnect(self, ctx):
        """Disconnects the bot from wavelink.Player and removes from the voice channel"""
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # Disconnect only if the user initiated the connection, server administrator or the guild owner
        if ctx.author.guild_permissions.administrator == False and ctx.guild.owner_id != ctx.author.id:
            if self.current_user.get(ctx.guild.id) != ctx.author.id:
                return await ctx.respond('You are not the one who queued this track or has insufficent admin permissions to do this.')

        # Check if there's even a voice client connected
        if not vc and not hasattr(vc, "connected"):
            return await ctx.respond('🎙️ Not currently connected to a voice channel.')

        # Check if we are playing a track before disconnecting
        if hasattr(vc, "playing") and hasattr(vc.current, "title"):
            # Store the title in the variable before stopping the track to notifiy the user since once it's stopped, vc.current.title will be None
            current_track_title = vc.current.title

            # Set pending disconnect state
            self.pendings.update({ctx.guild.id: "disconnecting"})

            await vc.stop()
            await ctx.send(f'⏹️ Stopped track: **{current_track_title}**')

        # Clear the enqueued tracks list and the current user record
        self.enqueued_tracks.pop(ctx.guild.id) if self.enqueued_tracks.get(ctx.guild.id) else None
        self.current_user.pop(ctx.guild.id) if self.current_user.get(ctx.guild.id) else None
        self.pendings.pop(ctx.guild.id) if self.pendings.get(ctx.guild.id) else None

        # Disconnect the bot from the voice channel
        await vc.disconnect()
        await ctx.respond('🔌 Disconnected.')
    
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.respond("❌ Sorry, this feature is not supported in DMs. Please use this command inside the guild.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(f"❌ You are missing the required permissions to use this command. Needed permissions:\n```{error}```")
        else:
            raise error

def setup(bot):
    bot.add_cog(Voice(bot))
