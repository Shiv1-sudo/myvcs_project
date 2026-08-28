"""Tag service."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.references.reference_manager import ReferenceManager


LOGGER = get_logger(__name__)


class TagService:
    """Manage tags."""

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

    def create_tag(
        self,
        tag_name: str,
    ) -> None:
        """Create lightweight tag."""

        commit_id = (
            self.references
            .get_head_commit()
        )

        self.references.create_tag(
            tag_name,
            commit_id,
        )

        LOGGER.info(
            "Tag created: %s",
            tag_name,
        )

    def list_tags(self) -> list[str]:
        """List tags."""

        return self.references.list_tags()