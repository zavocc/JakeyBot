class ToolManifest:
    tool_human_name = "Audio Tools"
    audio_editor_tool_description = "Edit audio, simply provide the description for editing, and EzAudio will do the rest"
    audio_generator_tool_description = "Generate audio from text using PlayHT (Legacy)"
    audio_generator_gemini_tool_description = "Generate audio from text using Gemini models with steerable speech"
    voice_cloner_tool_description = "Clone voices and perform TTS tasks from the given audio files"

    # Voices
    voices_playht_enum = [
        "Aaliyah", "Adelaide", "Angelo", "Arista", "Atlas", "Basil", "Briggs", "Calum", "Celeste",
        "Cheyenne", "Chip", "Cillian", "Deedee", "Eleanor", "Fritz", "Gail", "Indigo", "Jennifer",
        "Judy", "Mamaw", "Mason", "Mikail", "Mitch", "Nia", "Quinn", "Ruby", "Thunder"
    ]

    voices_gemini_enum = [
        "Zephyr", "Kore", "Orus", "Autonoe", "Umbriel", "Erinome", "Laomedeia", "Schedar", "Achird", "Sadachbia",
        "Puck", "Fenrir", "Aoede", "Enceladus", "Algieba", "Algenib", "Achernar", "Gacrux", "Zubenelgenubi", "Sadalager",
        "Charon", "Leda", "Callirrhoe", "Iapetus", "Despina", "Rasalgethi", "Alnilam", "Pulcherrima", "Vindemiatrix", "Sulafar"
    ]

    def __init__(self):
        self.tool_schema = [ 
            {
                "name": "audio_editor",
                "description": self.audio_editor_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "string",
                            "description": "The discord attachment URL of the audio file"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "The prompt for the model to add elements to the audio"
                        },
                        "edit_start_in_seconds": {
                            "type": "number",
                            "description": "The start time in seconds to edit the audio"
                        },
                        "edit_length_in_seconds": {
                            "type": "number",
                            "description": "The length in seconds to edit the audio"
                        }
                    },
                    "required": ["discord_attachment_url", "prompt"]
                }
            },
            {
                "name": "audio_generator",
                "description": self.audio_generator_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string"
                        },
                        "voice": {
                            "type": "string",
                            "enum": self.voices_playht_enum,
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "audio_generator_gemini",
                "description": self.audio_generator_gemini_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string"
                        },
                        "style": {
                            "type": "string",
                            "description": "Steer the speech style and can accept such as whisper, laughter, singing, sarcasm, accent, pace etc."
                        },
                        "voice": {
                            "type": "string",
                            "enum": self.voices_gemini_enum,
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "voice_cloner",
                "description": self.voice_cloner_tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "discord_attachment_url": {
                            "type": "string",
                            "description": "The discord attachment URL of the audio file"
                        },
                        "text": {
                            "type": "string",
                            "description": "The text for the target voice to dictate the text"
                        }
                    },
                    "required": ["discord_attachment_url", "text"]
                }
            }
        ]

        self.tool_schema_openai = [
            {
                "type": "function",
                "function": {
                    "name": "audio_editor",
                    "description": self.audio_editor_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "discord_attachment_url": {
                                "type": "string",
                                "description": "The discord attachment URL of the audio file"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The prompt for the model to add elements to the audio"
                            },
                            "edit_start_in_seconds": {
                                "type": "number",
                                "description": "The start time in seconds to edit the audio"
                            },
                            "edit_length_in_seconds": {
                                "type": "number",
                                "description": "The length in seconds to edit the audio"
                            }
                        },
                        "required": ["discord_attachment_url", "prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_generator",
                    "description": self.audio_generator_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string"
                            },
                            "voice": {
                                "type": "string",
                                "enum": self.voices_playht_enum,
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_generator_gemini",
                    "description": self.audio_generator_gemini_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string"
                            },
                            "voice": {
                                "type": "string",
                                "enum": self.voices_gemini_enum,
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "voice_cloner",
                    "description": self.voice_cloner_tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "discord_attachment_url": {
                                "type": "string",
                                "description": "The discord attachment URL of the audio file"
                            },
                            "text": {
                                "type": "string",
                                "description": "The text for the target voice to dictate the text"
                            }
                        },
                        "required": ["discord_attachment_url", "text"]
                    }
                }
            }
        ]