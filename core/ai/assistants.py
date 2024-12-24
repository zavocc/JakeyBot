import aiofiles
import yaml

# Assistants
class Assistants:
    # function to get the assistants
    @staticmethod
    async def set_assistant_type(assistant_name: str, type: int = 0):
        # 0 - chat_assistants
        # 1 - utility_assistants

        # Load the assistants from YAML file
        async with aiofiles.open("data/assistants.yaml", "r") as assistants:
            _assistants_data = yaml.safe_load(await assistants.read())

        if type == 0:
            _assistants_mode = _assistants_data["chat_assistants"]
        else:
            _assistants_mode = _assistants_data["utility_assistants"]

        # Return the assistant
        return _assistants_mode[assistant_name].strip()
