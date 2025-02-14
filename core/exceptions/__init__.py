class PollOffTopicRefusal(Exception):
    pass

class HistoryDatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message
        
class CustomErrorMessage(Exception):
    def __init__(self, message):
        self.message = message

class ModelAPIKeyUnset(Exception):
    def __init__(self, message):
        self.message = message

__all__ = [
    "HistoryDatabaseError",
    "CustomErrorMessage",
    "ModelAPIKeyUnset",
    "PollOffTopicRefusal"
]