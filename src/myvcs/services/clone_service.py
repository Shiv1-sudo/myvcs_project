"""Repository clone service."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger
from myvcs.remote.local_remote import LocalRemote
from myvcs.repository.repository_manager import RepositoryManager


LOGGER = get_logger(__name__)


class CloneService:
    """Clone a repository."""

    def __init__(
        self,
        configuration: ApplicationConfig,
    ):
        self.configuration = configuration

    def clone(
        self,
        remote_path: str,
        destination_path: str,
    ) -> None:
        """Clone repository."""

        try:
            source = RepositoryManager(
                Path(remote_path),
                self.configuration,
            )

            source.require_repository()

            destination = RepositoryManager(
                Path(destination_path),
                self.configuration,
            )

            destination.initialize()

            remote = LocalRemote(source)

            remote.fetch(
                destination
            )

            LOGGER.info(
                "Repository cloned: %s",
                destination_path,
            )

        except Exception as exc:
            LOGGER.exception(
                "Clone failed."
            )

            raise RepositoryError(
                "Unable to clone repository."
            ) from exc