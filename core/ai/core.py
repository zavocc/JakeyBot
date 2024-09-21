import discord
import yaml
# Defaults
class GenAIConfigDefaults:
    def __init__(self):
        self.generation_config = {
            "temperature": 0.5,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 8192,
        }

        self.safety_settings_config = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
        ]

        # Default model
        self.model_config = "gemini-1.5-flash-001"

        
class ModelsList:
    @staticmethod
    def get_models_list():
        # Load the models list from YAML file
        with open("data/models.yaml", "r") as models:
            _internal_model_data = yaml.safe_load(models)

        # Iterate through the models and merge them as dictionary
        # It has to be put here instead of the init class since decorators doesn't seem to reference self class attributes
        _model_choices = [
            discord.OptionChoice(f"{model['name']} - {model['description']}", model['model'])
            for model in _internal_model_data['gemini_models']
        ]
        del _internal_model_data
        return _model_choices
    
    @staticmethod
    def get_tools_list():
        # Load the tools list from YAML file
        with open("data/tools.yaml", "r") as models:
            _tools_list = yaml.safe_load(models)

        # Load tools metadata
        _tool_choices = [
            discord.OptionChoice(tools["ui_name"], tools['tool_name'])
            for tools in _tools_list
        ]
        del _tools_list
        return _tool_choices