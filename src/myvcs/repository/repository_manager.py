"""Repository management."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_constants import UTF8_ENCODING
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger


LOGGER = get_logger(__name__)


class RepositoryManager:
    """Manages the physical repository structure."""

    def __init__(
        self,
        working_directory: Path,
        configuration: ApplicationConfig,
    ):
        self.working_directory = (
            working_directory.resolve()
        )

        self.configuration = configuration

        metadata_directory_name = configuration.require(
            "repository",
            "metadata_directory",
        )

        objects_directory_name = configuration.require(
            "repository",
            "objects_directory",
        )

        references_directory_name = configuration.require(
            "repository",
            "references_directory",
        )

        heads_directory_name = configuration.require(
            "repository",
            "heads_directory",
        )

        tags_directory_name = configuration.require(
            "repository",
            "tags_directory",
        )

        index_file_name = configuration.require(
            "repository",
            "index_file",
        )

        head_file_name = configuration.require(
            "repository",
            "head_file",
        )

        repository_config_file_name = configuration.require(
            "repository",
            "repository_config_file",
        )

        self.metadata_directory = (
            self.working_directory
            / metadata_directory_name
        )

        self.objects_directory = (
            self.metadata_directory
            / objects_directory_name
        )

        self.references_directory = (
            self.metadata_directory
            / references_directory_name
        )

        self.heads_directory = (
            self.references_directory
            / heads_directory_name
        )

        self.tags_directory = (
            self.references_directory
            / tags_directory_name
        )

        self.index_file = (
            self.metadata_directory
            / index_file_name
        )

        self.head_file = (
            self.metadata_directory
            / head_file_name
        )

        self.repository_config_file = (
            self.metadata_directory
            / repository_config_file_name
        )

    def exists(self) -> bool:
        """Return whether a repository exists."""

        return self.metadata_directory.is_dir()

    def require_repository(self) -> None:
        """Raise an error if repository does not exist."""

        if not self.exists():
            raise RepositoryError(
                "No MyVCS repository found in "
                f"{self.working_directory}"
            )

    def initialize(self) -> None:
        """Initialize a new repository."""

        LOGGER.info(
            "Initializing repository: %s",
            self.working_directory,
        )

        try:
            directories = (
                self.metadata_directory,
                self.objects_directory,
                self.references_directory,
                self.heads_directory,
                self.tags_directory,
            )

            for directory in directories:
                directory.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            default_branch = self.configuration.require(
                "references",
                "default_branch",
            )

            head_prefix = self.configuration.require(
                "references",
                "head_prefix",
            )

            heads_prefix = self.configuration.require(
                "references",
                "heads_reference_prefix",
            )

            self.head_file.write_text(
                f"{head_prefix}"
                f"{heads_prefix}"
                f"{default_branch}\n",
                encoding=UTF8_ENCODING,
            )

            default_branch_file = (
                self.heads_directory
                / default_branch
            )

            default_branch_file.write_text(
                "",
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Repository initialized successfully."
            )

        except OSError as exc:
            LOGGER.exception(
                "Repository initialization failed."
            )

            raise RepositoryError(
                "Unable to initialize repository."
            ) from exc

    def relative_path(
        self,
        file_path: Path,
    ) -> str:
        """Return path relative to working directory."""

        try:
            return str(
                file_path.resolve().relative_to(
                    self.working_directory
                )
            )

        except ValueError as exc:
            raise RepositoryError(
                f"Path is outside repository: {file_path}"
            ) from exc