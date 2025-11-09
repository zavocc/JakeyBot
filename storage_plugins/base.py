from abc import ABC, abstractmethod
from typing import Any, Optional


class StoragePlugin(ABC):
    """Minimal interface all storage plugins must follow."""

    name: str = "base"

    def __init__(self, options: Optional[dict] = None):
        self.options = options or {}
        self.client: Any = None

    async def setup(self) -> None:
        """Optional async hook to initialize resources."""

    async def teardown(self) -> None:
        """Optional async hook to release resources."""

    @abstractmethod
    async def upload(self, file_path: str, file_name: str, client: Any = None) -> str:
        """Upload a file and return a retrievable URL/reference."""
