import yaml

# Assistants
class Assistants:
    def __init__(self):
        # Parse YAML file
        with open("data/assistants.yaml", "r") as f:
            assistants = yaml.safe_load(f)

        ###############################################
        # Gems
        ###############################################
        self.jakey_system_prompt = assistants["chat_assistants"]["jakey_system_prompt"]
        self.gemini_stock_system_prompt = assistants["chat_assistants"]["gemini_stock_system_prompt"]
        self.coding_partner_system_prompt = assistants["chat_assistants"]["coding_partner_system_prompt"]
        self.brainstormer_system_prompt = assistants["chat_assistants"]["brainstormer_system_prompt"]

        ###############################################
        # Utilities
        ###############################################
        # Discord text channel summarizer
        self.discord_msg_summarizer_prompt = assistants["utility_assistants"]["discord_msg_summarizer_prompt"]

        ###############################################
        # Apps
        ###############################################
        # Message rephraser
        self.message_rephraser_prompt = assistants["utility_assistants"]["message_rephraser_prompt"]
        # Message summarizer
        self.message_summarizer_prompt = assistants["utility_assistants"]["message_summarizer_prompt"]
        # Message suggester
        self.message_suggestions_prompt = assistants["utility_assistants"]["message_suggestions_prompt"]
