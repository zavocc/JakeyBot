class GeminiClientRequestError(Exception):
    def __init__(self, message: str, error_code: int = 400):
        self.error_code = error_code
        self.message = message

class HistoryDatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message

class MultiModalUnavailable(Exception):
    pass

class ModelUnavailable(ModuleNotFoundError):
    pass

class ToolsUnavailable(ModuleNotFoundError):
    pass

__all__ = [
    "GeminiClientRequestError",
    "HistoryDatabaseError",
    "ModelUnavailable",
    "MultiModalUnavailable",
    "ToolsUnavailable"
]