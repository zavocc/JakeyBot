# TODO: change error_message to just message
# Replace all occurrences in the codebase that uses error_message to message
class GeminiClientRequestError(Exception):
    def __init__(self, error_code: int = 400, error_message: str = "Bad Request"):
        self.error_code = error_code
        self.error_message = error_message

class HistoryDatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message

class MultiModalUnavailable(Exception):
    pass

class ModelUnavailable(ModuleNotFoundError):
    pass

class ToolsUnavailable(ModuleNotFoundError):
    pass

__all__ = [GeminiClientRequestError, HistoryDatabaseError, ModelUnavailable, MultiModalUnavailable, ToolsUnavailable]