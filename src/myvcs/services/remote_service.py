"""Remote operations."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger
from myvcs.remote.local_remote import LocalRemote
from myvcs.repository.repository_manager import RepositoryManager


LOGGER = get_logger(__name__)


class RemoteService:
    """Push and fetch operations."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

    def push(
        self,
        remote_path: str,
        branch_name: str,
    ) -> None:
        """Push to local remote."""

        try:
            remote_repository = (
                RepositoryManager(
                    Path(remote_path),
                    self.configuration,
                )
            )

            remote_repository.require_repository()

            remote = LocalRemote(
                remote_repository
            )

            remote.push(
                self.repository,
                branch_name,
            )

        except Exception as exc:
            LOGGER.exception(
                "Push failed."
            )

            raise RepositoryError(
                "Unable to push."
            ) from exc

    def fetch(
        self,
        remote_path: str,
    ) -> None:
        """Fetch from local remote."""

        try:
            remote_repository = (
                RepositoryManager(
                    Path(remote_path),
                    self.configuration,
                )
            )

            remote_repository.require_repository()

            remote = LocalRemote(
                remote_repository
            )

            remote.fetch(
                self.repository
            )

        except Exception as exc:
            LOGGER.exception(
                "Fetch failed."
            )

            raise RepositoryError(
                "Unable to fetch."
            ) from exc
     
    def pull(
        self,
        remote_path: str,
        branch_name: str,
    ) ->     None:
        """Fetch and fast-forward local branch."""

        self.fetch(
        remote_path
        )

        from myvcs.services.merge_service import (
        MergeService,
        )

        merge_service = MergeService(
            self.repository,
            self.configuration,
        )

        merge_service.merge(
        branch_name
        )

        LOGGER.info(
        "Pull completed: %s",
        branch_name,
    )      