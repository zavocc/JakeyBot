import discord
import yaml
        
class ModelsList:
    @staticmethod
    def get_models_list():
        # Load the models list from YAML file
        with open("data/models_openai.yaml", "r") as models:
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