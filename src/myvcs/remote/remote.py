"""Remote repository abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path


class Remote(ABC):
    """Abstract remote repository."""

    @abstractmethod
    def push(
        self,
        source_repository,
        branch_name: str,
    ) -> None:
        """Push branch."""

    @abstractmethod
    def fetch(
        self,
        target_repository,
    ) -> None:
        """Fetch remote objects."""