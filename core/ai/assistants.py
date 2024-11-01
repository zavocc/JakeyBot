import yaml

# Assistants
class Assistants:
    def __init__(self):
        # Parse YAML file
        with open("data/assistants.yaml", "r") as f:
            assistants = yaml.safe_load(f)

        # Jakey
        self.jakey_system_prompt = assistants["chat_assistants"]["jakey_system_prompt"].strip()
        # Discord text channel summarizer
        self.discord_msg_summarizer_prompt = assistants["utility_assistants"]["discord_msg_summarizer_prompt"].strip()

        ###############################################
        # Apps
        ###############################################
        # Message rephraser
        self.message_rephraser_prompt = assistants["utility_assistants"]["message_rephraser_prompt"].strip()
        # Message summarizer
        self.message_summarizer_prompt = assistants["utility_assistants"]["message_summarizer_prompt"].strip()
        # Message suggester
        self.message_suggestions_prompt = assistants["utility_assistants"]["message_suggestions_prompt"].strip()
