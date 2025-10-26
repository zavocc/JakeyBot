import yaml
import os
from typing import Any, Dict

class Config:
    def __init__(self, config_path: str = 'config.yaml'):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def bot_token(self) -> str:
        return self.get('bot.token')

    @property
    def bot_name(self) -> str:
        return self.get('bot.name', 'Jakey Bot')

    @property
    def bot_prefix(self) -> str:
        return self.get('bot.prefix', '$')
    
    @property
    def system_user_id(self) -> int:
        return self.get('bot.system_user_id')

    @property
    def max_context_history(self) -> int:
        return self.get('bot.max_context_history', 10)
    
    @property
    def shared_chat_history(self) -> bool:
        return self.get('bot.shared_chat_history', False)

    @property
    def mongo_db_url(self) -> str:
        return self.get('database.mongodb.url')

    @property
    def mongo_db_name(self) -> str:
        return self.get('database.mongodb.name', 'jakey_prod_db')

    @property
    def mongo_db_collection_name(self) -> str:
        return self.get('database.mongodb.collection_name', 'jakey_prod_db_collection')

    def get_api_key(self, service: str) -> str | None:
        return self.get(f'api_keys.{service}')

    @property
    def azure_ai_flux_endpoint(self) -> str:
        return self.get('azure.ai.flux_endpoint')
    
    @property
    def azure_ai_flux_key(self) -> str:
        return self.get('azure.ai.flux_key')

    @property
    def azure_ai_api_base(self) -> str:
        return self.get('azure.ai.api_base')
    
    @property
    def azure_ai_api_key(self) -> str:
        return self.get('azure.ai.api_key')

    @property
    def azure_storage_account_url(self) -> str:
        return self.get('azure.storage.account_url')
    
    @property
    def azure_storage_connection_string(self) -> str:
        return self.get('azure.storage.connection_string')
    
    @property
    def azure_storage_container_name(self) -> str:
        return self.get('azure.storage.container_name')
    
    @property
    def azure_tts_region(self) -> str:
        return self.get('azure.tts.region')
    
    @property
    def azure_subscription_id(self) -> str:
        return self.get('azure.subscription_id')
    
    @property
    def azure_access_token(self) -> str:
        return self.get('azure.access_token')

    @property
    def openrouter_site_url(self) -> str:
        return self.get('openrouter.site_url')
    
    @property
    def openrouter_app_name(self) -> str:
        return self.get('openrouter.app_name')

    @property
    def lavalink_uri(self) -> str:
        return self.get('lavalink.uri')
    
    @property
    def lavalink_password(self) -> str:
        return self.get('lavalink.password')

    @property
    def chroma_http_host(self) -> str:
        return self.get('chroma.http_host')
    
    @property
    def chroma_http_port(self) -> int:
        return self.get('chroma.http_port')

    @property
    def cse_search_engine_cxid(self) -> str:
        return self.get('cse.search_engine_cxid')

    @property
    def temp_dir(self) -> str:
        return self.get('admin.temp_dir', 'temp/')

# Global config instance
config = Config()
