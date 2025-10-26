"""
Configuration management for JakeyBot using YAML files.

This module provides a centralized way to load and access configuration
from YAML files, replacing the previous environ-based approach.
"""

import os
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path


class Config:
    """
    YAML-based configuration loader for JakeyBot.
    
    Provides both attribute-style and dictionary-style access to configuration values.
    Supports nested configuration sections and provides default values.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation (e.g., 'bot.name', 'ai_providers.openai.api_key')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key using dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def __getattr__(self, name: str) -> Any:
        """
        Attribute-style access to configuration sections.
        
        Args:
            name: Section name
            
        Returns:
            ConfigSection instance for the requested section
        """
        if name.startswith('_'):
            raise AttributeError(f"Invalid attribute name: {name}")
        
        if name in self._config:
            return ConfigSection(self._config[name])
        raise AttributeError(f"Configuration section not found: {name}")
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access to configuration."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-style setting of configuration values."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if configuration key exists."""
        return self.get(key) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            path: Optional path to save to (defaults to original path)
        """
        save_path = Path(path) if path else self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as file:
            yaml.dump(self._config, file, default_flow_style=False, allow_unicode=True)


class ConfigSection:
    """
    Wrapper for configuration sections to provide attribute-style access.
    """
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from this section."""
        return self._data.get(key, default)
    
    def __getattr__(self, name: str) -> Any:
        """Attribute-style access to section values."""
        if name.startswith('_'):
            raise AttributeError(f"Invalid attribute name: {name}")
        
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return ConfigSection(value)
            return value
        raise AttributeError(f"Configuration key not found: {name}")
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access to section values."""
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in this section."""
        return key in self._data
    
    def to_dict(self) -> Dict[str, Any]:
        """Return section data as dictionary."""
        return self._data.copy()


# Global configuration instance
_config_instance: Optional[Config] = None


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Config instance
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def reload_config() -> Config:
    """
    Reload configuration from file.
    
    Returns:
        Updated Config instance
    """
    global _config_instance
    if _config_instance is None:
        return load_config()
    else:
        _config_instance.reload()
        return _config_instance


# Convenience functions for common configuration access patterns
def get_bot_config() -> Dict[str, Any]:
    """Get bot configuration section."""
    return get_config().get('bot', {})


def get_database_config() -> Dict[str, Any]:
    """Get database configuration section."""
    return get_config().get('database', {})


def get_ai_providers_config() -> Dict[str, Any]:
    """Get AI providers configuration section."""
    return get_config().get('ai_providers', {})


def get_tools_config() -> Dict[str, Any]:
    """Get tools configuration section."""
    return get_config().get('tools', {})


def get_services_config() -> Dict[str, Any]:
    """Get services configuration section."""
    return get_config().get('services', {})


def get_admin_config() -> Dict[str, Any]:
    """Get admin configuration section."""
    return get_config().get('admin', {})


# Backward compatibility functions for environ-based code
def get_env(key: str, default: str = None) -> Optional[str]:
    """
    Get configuration value, supporting both YAML config and environment variables.
    
    This provides backward compatibility for code that still uses environ.get().
    
    Args:
        key: Configuration key (supports dot notation for YAML)
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    # First try YAML config
    config_value = get_config().get(key)
    if config_value is not None:
        return str(config_value)
    
    # Fallback to environment variable
    return os.environ.get(key, default)


def get_token() -> Optional[str]:
    """Get Discord bot token."""
    return get_env('bot.token') or get_env('TOKEN')


def get_bot_prefix() -> str:
    """Get bot command prefix."""
    return get_env('bot.prefix') or get_env('BOT_PREFIX', '$')


def get_bot_name() -> str:
    """Get bot name."""
    return get_env('bot.name') or get_env('BOT_NAME', 'Jakey Bot')


def get_mongo_url() -> Optional[str]:
    """Get MongoDB connection string."""
    return get_env('database.mongodb.url') or get_env('MONGO_DB_URL')


def get_mongo_db_name() -> str:
    """Get MongoDB database name."""
    return get_env('database.mongodb.name') or get_env('MONGO_DB_NAME', 'jakey_prod_db')


def get_mongo_collection_name() -> str:
    """Get MongoDB collection name."""
    return get_env('database.mongodb.collection_name') or get_env('MONGO_DB_COLLECTION_NAME', 'jakey_prod_collection')


def get_temp_dir() -> str:
    """Get temporary directory path."""
    return get_env('services.temp_dir') or get_env('TEMP_DIR', 'temp')


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for specified provider.
    
    Args:
        provider: API provider name (e.g., 'openai', 'gemini', 'anthropic')
        
    Returns:
        API key for the provider
    """
    # Handle special cases for different config key names
    if provider == 'exa':
        config_key = 'tools.search.exa_ai_key'
    elif provider == 'youtube':
        config_key = 'tools.youtube.api_key'
    elif provider == 'github':
        config_key = 'tools.github.token'
    elif provider == 'huggingface':
        config_key = 'tools.huggingface.token'
    elif provider == 'fal':
        config_key = 'services.fal.key'
    else:
        config_key = f'ai_providers.{provider}.api_key'
    
    env_key = f'{provider.upper()}_API_KEY'
    if provider == 'github':
        env_key = 'GITHUB_TOKEN'
    elif provider == 'huggingface':
        env_key = 'HF_TOKEN'
    elif provider == 'fal':
        env_key = 'FAL_KEY'
    elif provider == 'exa':
        env_key = 'EXA_AI_KEY'
    elif provider == 'youtube':
        env_key = 'YOUTUBE_DATA_v3_API_KEY'
    
    return get_env(config_key) or get_env(env_key)