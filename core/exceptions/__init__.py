class ChatHistoryFull(Exception):
    def __init__(self, message):
        super().__init__(message)

class MultiModalUnavailable(Exception):
    def __init__(self, message):
        super().__init__(message)

__all__ = [ChatHistoryFull, MultiModalUnavailable]