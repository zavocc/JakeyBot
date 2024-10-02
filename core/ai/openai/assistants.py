import yaml

# Assistants
class Assistants:
    def __init__(self):
        # Parse YAML file
        with open("data/assistants.yaml", "r") as f:
            assistants = yaml.safe_load(f)

        # Jakey
        self.jakey_system_prompt = assistants["chat_assistants"]["jakey_system_prompt"]