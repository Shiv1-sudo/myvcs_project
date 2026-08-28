"""Merge service."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import CommitError
from myvcs.common.application_logging import get_logger
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore
from myvcs.services.checkout_service import CheckoutService


LOGGER = get_logger(__name__)


class MergeService:
    """Merge branches."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.references = ReferenceManager(
            repository,
            configuration,
        )

        self.object_store = ObjectStore(
            repository.objects_directory,
            configuration,
        )

        self.checkout_service = CheckoutService(
            repository,
            configuration,
        )

    def merge(
        self,
        source_branch: str,
    ) -> str:
        """Perform a fast-forward merge."""

        try:
            current_commit = (
                self.references
                .get_head_commit()
            )

            source_commit = (
                self.references
                .get_branch_commit(
                    source_branch
                )
            )

            if not source_commit:
                raise CommitError(
                    f"Branch not found: {source_branch}"
                )

            if current_commit == source_commit:
                return current_commit

            if not self._contains_commit(
                source_commit,
                current_commit,
            ):
                raise CommitError(
                    "Non-fast-forward merge is not "
                    "implemented yet."
                )

            source = self.object_store.read(
                source_commit
            )

            self.checkout_service._restore_tree(
                source.tree_id
            )

            self.references.update_head(
                source_commit
            )

            LOGGER.info(
                "Fast-forward merge completed: %s",
                source_commit,
            )

            return source_commit

        except CommitError:
            raise

        except Exception as exc:
            LOGGER.exception(
                "Merge failed."
            )

            raise CommitError(
                "Unable to merge branch."
            ) from exc

    def _contains_commit(
        self,
        start_id: str,
        target_id: str | None,
    ) -> bool:
        """Determine whether target is ancestor."""

        current = start_id

        while current:
            if current == target_id:
                return True

            commit = self.object_store.read(
                current
            )

            current = commit.parent_id

        return False