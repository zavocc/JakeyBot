class MultiModalUnavailable(Exception):
    pass

class ModelUnavailable(ModuleNotFoundError):
    pass

class ToolsUnavailable(ModuleNotFoundError):
    pass

__all__ = [ModelUnavailable, MultiModalUnavailable, ToolsUnavailable]