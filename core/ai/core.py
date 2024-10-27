import discord
import yaml

class ModelsList:
    @staticmethod
    def get_models_list(raw=False):
        # Load the models list from YAML file
        with open("data/models.yaml", "r") as models:
            _internal_model_data = yaml.safe_load(models)

        # Iterate through the models and yield each as a discord.OptionChoice
        for model in _internal_model_data:
            if raw:
                yield model["model"]
            else:
                # Check if the model dict has hide_ui key
                if model.get("hide_ui") is not None and model.get("hide_ui") == True:
                    continue

                yield discord.OptionChoice(f"{model['name']} - {model['description']}", model["model"])
        
        del _internal_model_data

    @staticmethod
    def get_tools_list():
        # Load the tools list from YAML file
        with open("data/tools.yaml", "r") as tools:
            _tools_list = yaml.safe_load(tools)

        # Iterate through the tools and yield each as a discord.OptionChoice
        for tool in _tools_list:
            yield discord.OptionChoice(tool["ui_name"], tool['tool_name'])
        
        del _tools_list