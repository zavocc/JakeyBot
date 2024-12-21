class GeminiClientRequestError(Exception):
    def __init__(self, message: str, error_code: int = 400):
        self.error_code = error_code
        self.message = message

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
    pass


__all__ = [
    "GeminiClientRequestError",
    "HistoryDatabaseError",
    "ModelUnavailable",
    "MultiModalUnavailable",
    "SafetyFilterError",
    "ToolsUnavailable"
]