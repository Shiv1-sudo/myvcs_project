
"""Repository backup service."""

import shutil
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger
from myvcs.repository.repository_manager import RepositoryManager


LOGGER = get_logger(__name__)


class BackupService:
    """Create filesystem backups of a MyVCS repository."""

    def __init__(
        self,
        repository: RepositoryManager,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

    def backup(
        self,
        backup_path: str,
    ) -> Path:
        """Create a backup of the repository metadata."""

        self.repository.require_repository()

        source = self.repository.metadata_directory.resolve()
        destination = Path(backup_path).expanduser().resolve()

        # Check this first because the repository metadata directory
        # already exists and must never be used as the backup target.
        if destination == source:
            raise RepositoryError(
                "Backup destination cannot be the repository metadata directory."
            )

        if destination.exists():
            raise RepositoryError(
                f"Backup destination already exists: {destination}"
            )

        try:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copytree(
                source,
                destination,
            )

        except OSError as exc:
            LOGGER.exception(
                "Repository backup failed.",
            )

            raise RepositoryError(
                f"Unable to create repository backup: {destination}"
            ) from exc

        LOGGER.info(
            "Repository backup created: %s",
            destination,
        )

        return destination
 
