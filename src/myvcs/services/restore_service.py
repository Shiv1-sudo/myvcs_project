"""Repository restore service."""

import shutil
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger
from myvcs.repository.repository_manager import RepositoryManager

LOGGER = get_logger(__name__)


class RestoreService:
    """Restore a MyVCS repository from a filesystem backup."""

    def __init__(
        self,
        repository: RepositoryManager,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

    def restore(
        self,
        backup_path: str,
    ) -> None:
        """Restore repository metadata from a backup."""

        backup = Path(backup_path).expanduser().resolve()

        if not backup.is_dir():
            raise RepositoryError(
                f"Backup directory does not exist: {backup}"
            )

        metadata_directory = self.repository.metadata_directory.resolve()

        if backup == metadata_directory:
            raise RepositoryError(
                "Backup source cannot be the repository metadata directory."
            )

        try:
            if metadata_directory.exists():
                shutil.rmtree(metadata_directory)

            metadata_directory.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copytree(
                backup,
                metadata_directory,
            )

        except OSError as exc:
            LOGGER.exception("Repository restore failed.")

            raise RepositoryError(
                f"Unable to restore repository from backup: {backup}"
            ) from exc

        LOGGER.info(
            "Repository restored from backup: %s",
            backup,
        )