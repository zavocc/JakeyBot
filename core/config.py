"""
Configuration management module for JakeyBot.
Loads configuration from YAML file instead of environment variables.
"""
from pathlib import Path
from typing import Any, Optional
import logging
import yaml


class Config:
    """
    Configuration manager that loads settings from config.yaml.
    Provides a centralized way to access configuration values without using os.environ.
    """

    _instance = None
    _config = None

    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the configuration by loading the YAML file."""
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: str = "config.yaml"):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration file (default: config.yaml)

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file '{config_path}' not found. "
                f"Please copy 'config.yaml.template' to 'config.yaml' and configure it."
            )

        try:
            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
                logging.info("Configuration loaded successfully from %s", config_path)
        except yaml.YAMLError as e:
            logging.error("Failed to parse configuration file: %s", e)
            raise

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the config value (e.g., 'discord.token')
            default: Default value if key is not found or is None

        Returns:
            The configuration value or default if not found

        Example:
            config.get('discord.token')
            config.get('api_keys.openai_api_key')
            config.get('mongodb.url', 'mongodb://localhost:27017')
        """
        if self._config is None:
            self.load_config()

        keys = key_path.split('.')
        value = self._config

        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return default

            # Return default if value is None (explicitly set to null in YAML)
            return value if value is not None else default
        except (KeyError, TypeError, AttributeError):
            return default

    def get_discord_config(self) -> dict:
        """Get all Discord-related configuration."""
        return self._config.get('discord', {})

    def get_api_keys(self) -> dict:
        """Get all API keys configuration."""
        return self._config.get('api_keys', {})

    def get_mongodb_config(self) -> dict:
        """Get all MongoDB-related configuration."""
        return self._config.get('mongodb', {})

    def get_system_config(self) -> dict:
        """Get all system-related configuration."""
        return self._config.get('system', {})

    def get_tools_config(self) -> dict:
        """Get all tools-related configuration."""
        return self._config.get('tools', {})

    def validate_required_config(self):
        """
        Validate that required configuration values are present.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        # Check required Discord token
        token = self.get('discord.token')
        if not token or token == 'INSERT_DISCORD_TOKEN':
            raise ValueError("Please set a valid Discord bot token in config.yaml")

        logging.info("Required configuration validated successfully")


# Global config instance
config = Config()
