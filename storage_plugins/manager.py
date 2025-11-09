from __future__ import annotations

import importlib
import inspect
import logging
from os import environ
from pathlib import Path
from typing import Optional, Type

import yaml

from .base import StoragePlugin

_PLUGIN_INSTANCE: Optional[StoragePlugin] = None
_PLUGIN_READY = False


def _default_config() -> dict:
    return {
        "plugin": "storage_plugins.azure_blob.AzureBlobStoragePlugin",
        "options": {
            "connection_string_env": "AZURE_STORAGE_CONNECTION_STRING",
            "container_env": "AZURE_STORAGE_CONTAINER_NAME",
        },
    }


def _load_config() -> dict:
    _config_path = Path(environ.get("STORAGE_PLUGIN_CONFIG", "data/storage_plugins.yaml"))
    if not _config_path.exists():
        logging.info("Storage plugin config %s not found, using defaults.", _config_path)
        return _default_config()

    with _config_path.open("r", encoding="utf-8") as _config_file:
        _raw_config = yaml.safe_load(_config_file) or {}

    # Allow the yaml to either directly describe the plugin or wrap it in a top-level key.
    if "storage_plugin" in _raw_config:
        _raw_config = _raw_config["storage_plugin"] or {}

    _plugin_path = _raw_config.get("plugin")
    if not _plugin_path:
        logging.warning("No plugin specified in %s, falling back to defaults.", _config_path)
        return _default_config()

    return {
        "plugin": _plugin_path,
        "options": _raw_config.get("options") or {},
    }


def _import_plugin(_plugin_path: str) -> Type[StoragePlugin]:
    _module_path, _class_name = _plugin_path.rsplit(".", 1)
    _module = importlib.import_module(_module_path)
    _plugin_cls = getattr(_module, _class_name)
    if not issubclass(_plugin_cls, StoragePlugin):
        raise TypeError(f"{_plugin_path} is not a StoragePlugin implementation.")
    return _plugin_cls


async def get_storage_plugin() -> StoragePlugin:
    global _PLUGIN_INSTANCE, _PLUGIN_READY

    if _PLUGIN_INSTANCE is None:
        _config = _load_config()
        _plugin_cls = _import_plugin(_config["plugin"])
        _PLUGIN_INSTANCE = _plugin_cls(_config.get("options"))

    if not _PLUGIN_READY:
        _setup_result = _PLUGIN_INSTANCE.setup()
        if inspect.isawaitable(_setup_result):
            await _setup_result
        _PLUGIN_READY = True

    return _PLUGIN_INSTANCE


async def shutdown_storage_plugin() -> None:
    global _PLUGIN_READY
    if _PLUGIN_INSTANCE and _PLUGIN_READY:
        _teardown_result = _PLUGIN_INSTANCE.teardown()
        if inspect.isawaitable(_teardown_result):
            await _teardown_result
        _PLUGIN_READY = False
