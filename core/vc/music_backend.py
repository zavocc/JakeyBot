import importlib
class MusicAudioBackend:
    def __init__(self, bot):
        # pass the bot instance to this class
        self.bot = bot

        # Check if we can import wavelink otherwise we can't use the music backend
        try:
            self.wavelink = importlib.import_module("wavelink")
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Playback support is disabled: wavelink is not installed")
        
    def initialize(self):
        # TODO: move all the wavelink setup code here
        pass
