class HistoryDatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message

class MultiModalUnavailable(Exception):
    def __init__(self, message):
        self.message = message

class ModelUnavailable(ModuleNotFoundError):
    def __init__(self, message):
        self.message = message

class ToolsUnavailable(ModuleNotFoundError):
    def __init__(self, message):
        self.message = message

class SafetyFilterError(Exception):
    def __init__(self, reason=None):
        self.reason = reason


__all__ = [
    "HistoryDatabaseError",
    "ModelUnavailable",
    "MultiModalUnavailable",
    "SafetyFilterError",
    "ToolsUnavailable"
]