import openai
import os
import random

class BaseTextToSpeech:
    def __init__(self, prompt: str):
        self.prompt = prompt

    # Speech generation
    async def generate_speech(self):
        # Initiate OpenAI client
        client = openai.AsyncOpenAI()

        # Set temporary directory to store generated speech
        audio_file_path = f"{os.environ.get('TEMP_DIR')}/{random.randint(69310, 158165)}.JAKEYVOICE.mp3"
        
        # There is a limit on the character count to 4096, so we just instead tell the user to check their chat instead for output
        if len(self.prompt) > 4096:
            response = "Hey there! Sorry, I cannot understand your request because its too long... But, I sent you the message instead"
        else:
            response = self.prompt

        # Generate speech
        synthesis = await client.audio.speech.create(
            model="tts-1-hd",
            voice="echo",
            input=response,
            response_format="aac"
        )

        # Save speech to file to stream it later
        synthesis.write_to_file(audio_file_path)
        return audio_file_path
