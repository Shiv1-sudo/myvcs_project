"""Staging index implementation."""

import json
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_constants import UTF8_ENCODING
from myvcs.common.application_exceptions import StagingError
from myvcs.common.application_logging import get_logger

LOGGER = get_logger(__name__)


class StagingIndex:
    """Stores files staged for the next commit."""

    def __init__(
        self,
        index_file: Path,
        configuration: ApplicationConfig,
    ):
        self.index_file = index_file
        self.configuration = configuration

    def load(self) -> dict[str, str]:
        """Load staged entries."""

        try:
            if not self.index_file.exists():
                return {}

            content = self.index_file.read_text(encoding=UTF8_ENCODING)

            if not content.strip():
                return {}

            entries = json.loads(content)

            if not isinstance(entries, dict):
                raise StagingError("Staging index must contain an object.")

            return {str(path): str(object_id) for path, object_id in entries.items()}

        except StagingError:
            raise

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            LOGGER.exception("Unable to load staging index.")

            raise StagingError("Unable to load staging index.") from exc

    def save(
        self,
        entries: dict[str, str],
    ) -> None:
        """Persist staged entries."""

        try:
            self.index_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.index_file.write_text(
                json.dumps(
                    entries,
                    indent=2,
                    sort_keys=True,
                ),
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Staging index saved. Entries: %d",
                len(entries),
            )

        except OSError as exc:
            LOGGER.exception("Unable to save staging index.")

            raise StagingError("Unable to save staging index.") from exc

    def add(
        self,
        relative_path: str,
        object_id: str,
    ) -> None:
        """Add an object to the staging area."""

        entries = self.load()

        entries[relative_path] = object_id

        self.save(entries)

        LOGGER.info(
            "File staged: %s",
            relative_path,
        )

    def remove(
        self,
        relative_path: str,
    ) -> None:
        """Remove a path from the staging area."""

        entries = self.load()

        entries.pop(
            relative_path,
            None,
        )

        self.save(entries)

    # new code
    def clear(self) -> None:
        """Clear all staged entries."""

        self.save({})

        LOGGER.info("Staging index cleared.")
