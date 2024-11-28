class GeminiClientRequestError(Exception):
    def __init__(self, error_code: int = 400, error_message: str = "Bad Request"):
        self.error_code = error_code
        self.error_message = error_message

class MultiModalUnavailable(Exception):
    pass

class ModelUnavailable(ModuleNotFoundError):
    pass

class ToolsUnavailable(ModuleNotFoundError):
    pass

__all__ = [ModelUnavailable, MultiModalUnavailable, ToolsUnavailable]