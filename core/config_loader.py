# Configuration loader module

import os
import yaml
from typing import Dict, Any, Optional, Union

class Config:
    """
    Configuration class to load and manage settings from a YAML file and environment variables.
    """
    def __init__(self, config_path: str = 'config.yaml', template_path: str = 'config.yaml.template'):
        self.config_path = config_path
        self.template_path = template_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads configuration from the YAML file.
        If the config file doesn't exist, it creates one from the template.
        Environment variables override file settings.
        """
        if not os.path.exists(self.config_path):
            if os.path.exists(self.template_path):
                # Create config from template
                with open(self.template_path, 'r') as template_file:
                    config_data = yaml.safe_load(template_file)
                with open(self.config_path, 'w') as config_file:
                    yaml.dump(config_data, config_file, default_flow_style=False)
            else:
                # This case should ideally not happen if the template is always present
                config_data = {}
        else:
            with open(self.config_path, 'r') as file:
                config_data = yaml.safe_load(file) or {}

        # Helper function to safely get and set values from environment variables
        def _get_env_override(main_key, sub_key, default_value=None, is_bool=False):
            # Ensure main_key exists and is a dictionary
            if not isinstance(config_data.get(main_key), dict):
                config_data[main_key] = {}

            # Get value from YAML or default
            yaml_value = config_data[main_key].get(sub_key, default_value)

            # Override with environment variable
            env_value = os.getenv(sub_key.upper(), yaml_value) # Convention: ENV_VARS are uppercase

            if is_bool:
                return str(env_value).lower() == 'true'
            return env_value

        def _get_env_override_direct(key, default_value=None, is_bool=False):
            yaml_value = config_data.get(key, default_value)
            env_value = os.getenv(key.upper(), yaml_value)
            if is_bool:
                return str(env_value).lower() == 'true'
            return env_value

        # Override with environment variables
        # Bot settings
        bot_settings = config_data.setdefault('bot_settings', {})
        if not isinstance(bot_settings, dict): bot_settings = config_data['bot_settings'] = {} # Ensure it's a dict
        bot_settings['BOT_NAME'] = os.getenv('BOT_NAME', bot_settings.get('BOT_NAME'))
        bot_settings['BOT_PREFIX'] = os.getenv('BOT_PREFIX', bot_settings.get('BOT_PREFIX'))
        bot_settings['TEMP_DIR'] = os.getenv('TEMP_DIR', bot_settings.get('TEMP_DIR'))
        bot_settings['SHARED_CHAT_HISTORY'] = str(os.getenv('SHARED_CHAT_HISTORY', bot_settings.get('SHARED_CHAT_HISTORY', False))).lower() == 'true'

        # Discord Token
        config_data['TOKEN'] = os.getenv('TOKEN', config_data.get('TOKEN'))

        # API Providers
        api_providers = config_data.setdefault('api_providers', {})
        if not isinstance(api_providers, dict): api_providers = config_data['api_providers'] = {}
        api_providers['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', api_providers.get('GEMINI_API_KEY'))
        api_providers['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', api_providers.get('OPENAI_API_KEY'))
        api_providers['MISTRAL_API_KEY'] = os.getenv('MISTRAL_API_KEY', api_providers.get('MISTRAL_API_KEY'))
        api_providers['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', api_providers.get('ANTHROPIC_API_KEY'))
        api_providers['XAI_API_KEY'] = os.getenv('XAI_API_KEY', api_providers.get('XAI_API_KEY'))
        api_providers['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', api_providers.get('GROQ_API_KEY'))
        api_providers['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', api_providers.get('OPENROUTER_API_KEY'))
        api_providers['OPENAI_API_ENDPOINT'] = os.getenv('OPENAI_API_ENDPOINT', api_providers.get('OPENAI_API_ENDPOINT'))
        api_providers['LITELLM_DEBUG'] = str(os.getenv('LITELLM_DEBUG', api_providers.get('LITELLM_DEBUG', False))).lower() == 'true'

        # OpenRouter Ranking (optional)
        if isinstance(api_providers, dict): # api_providers is guaranteed to be a dict here
            or_ranking_data_from_yaml = api_providers.get('openrouter_ranking', {})
            if not isinstance(or_ranking_data_from_yaml, dict): or_ranking_data_from_yaml = {}

            or_site_url = os.getenv('OR_SITE_URL', or_ranking_data_from_yaml.get('OR_SITE_URL'))
            or_app_name = os.getenv('OR_APP_NAME', or_ranking_data_from_yaml.get('OR_APP_NAME'))

            if or_site_url or or_app_name:
                api_providers['openrouter_ranking'] = {
                    'OR_SITE_URL': or_site_url,
                    'OR_APP_NAME': or_app_name
                }
            elif 'openrouter_ranking' in api_providers: # if it exists from YAML but env vars make it empty
                del api_providers['openrouter_ranking']


        # Database
        database_settings = config_data.setdefault('database', {})
        if not isinstance(database_settings, dict): database_settings = config_data['database'] = {}
        database_settings['MONGO_DB_URL'] = os.getenv('MONGO_DB_URL', database_settings.get('MONGO_DB_URL'))
        database_settings['MONGO_DB_NAME'] = os.getenv('MONGO_DB_NAME', database_settings.get('MONGO_DB_NAME'))
        database_settings['MONGO_DB_COLLECTION_NAME'] = os.getenv('MONGO_DB_COLLECTION_NAME', database_settings.get('MONGO_DB_COLLECTION_NAME'))

        # Tool Keys
        tool_keys = config_data.setdefault('tool_keys', {})
        if not isinstance(tool_keys, dict): tool_keys = config_data['tool_keys'] = {}
        tool_keys['BING_SUBSCRIPTION_KEY'] = os.getenv('BING_SUBSCRIPTION_KEY', tool_keys.get('BING_SUBSCRIPTION_KEY'))
        tool_keys['YOUTUBE_DATA_V3_API_KEY'] = os.getenv('YOUTUBE_DATA_V3_API_KEY', tool_keys.get('YOUTUBE_DATA_V3_API_KEY'))
        tool_keys['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN', tool_keys.get('GITHUB_TOKEN'))

        # Services - Azure Storage
        services_settings = config_data.setdefault('services', {})
        if not isinstance(services_settings, dict): services_settings = config_data['services'] = {}

        azure_storage_data = services_settings.setdefault('azure_storage', {})
        if not isinstance(azure_storage_data, dict): azure_storage_data = services_settings['azure_storage'] = {}

        azure_storage_data['AZURE_STORAGE_ACCOUNT_URL'] = os.getenv('AZURE_STORAGE_ACCOUNT_URL', azure_storage_data.get('AZURE_STORAGE_ACCOUNT_URL'))
        azure_storage_data['AZURE_STORAGE_CONNECTION_STRING'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING', azure_storage_data.get('AZURE_STORAGE_CONNECTION_STRING'))
        azure_storage_data['AZURE_STORAGE_CONTAINER_NAME'] = os.getenv('AZURE_STORAGE_CONTAINER_NAME', azure_storage_data.get('AZURE_STORAGE_CONTAINER_NAME'))

        if not any(azure_storage_data.values()):
            if 'azure_storage' in services_settings:
                 del services_settings['azure_storage']
            if not services_settings: # if services dict itself becomes empty
                 del config_data['services']

        return config_data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value by key.
        Nested keys can be accessed using dot notation (e.g., "database.MONGO_DB_URL").
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def __getitem__(self, key: str) -> Any:
        """
        Allows dictionary-style access to configuration values.
        """
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """
        Allows checking for key existence using 'in' operator.
        """
        return self.get(key) is not None

# Global config instance (optional, can be instantiated where needed)
# config = Config()
# Example usage:
# token = config.get("TOKEN")
# bot_name = config.get("bot_settings.BOT_NAME")
# print(f"Bot Name: {bot_name}, Token: {'present' if token else 'missing'}")
# print(f"Mongo URL: {config.get('database.MONGO_DB_URL', 'Not Set')}")
# print(f"Gemini Key: {config.get('api_providers.GEMINI_API_KEY', 'Not Set')}")
# print(f"Azure Storage Container: {config.get('services.azure_storage.AZURE_STORAGE_CONTAINER_NAME', 'Not Set')}")
# print(f"Shared chat history: {config.get('bot_settings.SHARED_CHAT_HISTORY')}")
# print(f"LiteLLM Debug: {config.get('api_providers.LITELLM_DEBUG')}")

# Ensure the template path is correct if this script is run directly for testing
if __name__ == '__main__':
    # This assumes the script is in core/ and config.yaml.template is in the root
    # Adjust path if necessary for direct execution
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_config_path = os.path.join(project_root, 'config.yaml.template')
    actual_config_path = os.path.join(project_root, 'config.yaml')

    print(f"Looking for template at: {template_config_path}")
    print(f"Looking for config at: {actual_config_path}")

    # Create a dummy template if it doesn't exist for testing
    if not os.path.exists(template_config_path):
        print(f"Creating dummy template for testing: {template_config_path}")
        dummy_template_content = {
            'bot_settings': {'BOT_NAME': 'TestBot', 'BOT_PREFIX': '!'},
            'TOKEN': 'test_token',
            'api_providers': {'GEMINI_API_KEY': 'test_gemini'},
            'database': {'MONGO_DB_URL': 'mongodb://localhost:27017'},
            'tool_keys': {},
            'services': {'azure_storage': {'AZURE_STORAGE_CONTAINER_NAME': 'testcontainer'}}
        }
        with open(template_config_path, 'w') as f:
            yaml.dump(dummy_template_content, f)

    # Test with specific paths
    config_instance = Config(config_path=actual_config_path, template_path=template_config_path)

    print(f"Bot Name from config: {config_instance.get('bot_settings.BOT_NAME')}")
    print(f"Token from config: {config_instance.get('TOKEN')}")
    # Set an environment variable to test override
    os.environ['BOT_NAME'] = "EnvBotName"
    os.environ['TOKEN'] = "EnvToken"
    os.environ['MONGO_DB_URL'] = "env_mongodb_url"
    os.environ['LITELLM_DEBUG'] = "true"
    os.environ['SHARED_CHAT_HISTORY'] = "true"

    # Reload config to see environment variable overrides
    config_instance_env_override = Config(config_path=actual_config_path, template_path=template_config_path)
    print(f"Bot Name (after env override): {config_instance_env_override.get('bot_settings.BOT_NAME')}")
    assert config_instance_env_override.get('bot_settings.BOT_NAME') == "EnvBotName"
    print(f"Token (after env override): {config_instance_env_override.get('TOKEN')}")
    assert config_instance_env_override.get('TOKEN') == "EnvToken"
    print(f"Mongo URL (after env override): {config_instance_env_override.get('database.MONGO_DB_URL')}")
    assert config_instance_env_override.get('database.MONGO_DB_URL') == "env_mongodb_url"
    print(f"LiteLLM Debug (after env override): {config_instance_env_override.get('api_providers.LITELLM_DEBUG')}")
    assert config_instance_env_override.get('api_providers.LITELLM_DEBUG') is True
    print(f"Shared History (after env override): {config_instance_env_override.get('bot_settings.SHARED_CHAT_HISTORY')}")
    assert config_instance_env_override.get('bot_settings.SHARED_CHAT_HISTORY') is True


    # Clean up dummy config and template if they were created
    if os.path.exists(actual_config_path) and "test_token" in open(actual_config_path).read():
        os.remove(actual_config_path)
    if os.path.exists(template_config_path) and "TestBot" in open(template_config_path).read():
         os.remove(template_config_path)
    print("Test completed.")
