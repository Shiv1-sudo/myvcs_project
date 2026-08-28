"""Branch management."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import ReferenceError
from myvcs.common.application_logging import get_logger
from myvcs.references.reference_manager import ReferenceManager

LOGGER = get_logger(__name__)


class BranchService:
    """Manage branches."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.reference_manager = ReferenceManager(
            repository,
            configuration,
        )

    def list_branches(self) -> list[str]:
        """Return local branches."""

        try:
            return self.reference_manager.list_branches()

        except Exception as exc:
            LOGGER.exception("Unable to list branches.")
            raise ReferenceError("Unable to list branches.") from exc

    def create_branch(
        self,
        branch_name: str,
    ) -> None:
        """Create branch at HEAD."""

        try:
            commit_id = self.reference_manager.get_head_commit()

            self.reference_manager.create_branch(
                branch_name,
                commit_id,
            )

            LOGGER.info(
                "Branch created: %s",
                branch_name,
            )

        except Exception as exc:
            LOGGER.exception("Unable to create branch.")
            raise ReferenceError("Unable to create branch.") from exc
