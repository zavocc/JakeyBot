from core.abc import Typehint_StoragePlugin
from typing import Literal
import aiofiles
import importlib
import yaml

# TODO: Implement exposure of client objects so it can be started in #main.py
async def init_plugins():
    pass

async def load_plugin(plugin_type: Literal['storage']) -> Typehint_StoragePlugin:
    if plugin_type == 'storage':
        
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")
