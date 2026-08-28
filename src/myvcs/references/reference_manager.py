"""Reference management."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_constants import UTF8_ENCODING
from myvcs.common.application_exceptions import ReferenceError
from myvcs.common.application_logging import get_logger

LOGGER = get_logger(__name__)


class ReferenceManager:
    """Manages HEAD, branch, and tag references."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

    def current_branch(self) -> str:
        """Return current branch name."""

        try:
            head_content = self.repository.head_file.read_text(
                encoding=UTF8_ENCODING
            ).strip()

            head_prefix = self.configuration.require(
                "references",
                "head_prefix",
            )

            reference_prefix = self.configuration.require(
                "references",
                "heads_reference_prefix",
            )

            if not head_content.startswith(head_prefix):
                raise ReferenceError("HEAD is not a symbolic reference.")

            reference = head_content[len(head_prefix) :]

            if not reference.startswith(reference_prefix):
                raise ReferenceError(f"Invalid HEAD reference: {reference}")

            return reference[len(reference_prefix) :]

        except OSError as exc:
            LOGGER.exception("Unable to read HEAD.")

            raise ReferenceError("Unable to read HEAD.") from exc

    def current_branch_file(self):
        """Return current branch reference file."""

        branch_name = self.current_branch()

        return self.repository.heads_directory / branch_name

    def get_branch_file(
        self,
        branch_name: str,
    ):
        """Return the reference file for a branch."""

        if not branch_name:
            raise ReferenceError("Branch name cannot be empty.")

        return self.repository.heads_directory / branch_name

    def get_branch_commit(
        self,
        branch_name: str,
    ) -> str | None:
        """Return the commit ID referenced by a branch."""

        try:
            branch_file = self.get_branch_file(branch_name)

            if not branch_file.exists():
                raise ReferenceError(f"Branch does not exist: {branch_name}")

            commit_id = branch_file.read_text(encoding=UTF8_ENCODING).strip()

            return commit_id or None

        except OSError as exc:
            LOGGER.exception("Unable to read branch reference.")

            raise ReferenceError(
                f"Unable to read branch reference: {branch_name}"
            ) from exc

    def get_head_commit(self) -> str | None:
        """Return commit ID of the current branch."""

        try:
            branch_file = self.current_branch_file()

            if not branch_file.exists():
                return None

            commit_id = branch_file.read_text(encoding=UTF8_ENCODING).strip()

            return commit_id or None

        except OSError as exc:
            LOGGER.exception("Unable to read branch reference.")

            raise ReferenceError("Unable to read branch reference.") from exc

    def update_head(
        self,
        commit_id: str,
    ) -> None:
        """Move current branch to a commit."""

        try:
            branch_file = self.current_branch_file()

            branch_file.write_text(
                f"{commit_id}\n",
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Branch moved to commit: %s",
                commit_id,
            )

        except OSError as exc:
            LOGGER.exception("Unable to update branch reference.")

            raise ReferenceError("Unable to update branch reference.") from exc

    def checkout_branch(
        self,
        branch_name: str,
    ) -> None:
        """Make HEAD point to the specified branch."""

        try:
            branch_file = self.get_branch_file(branch_name)

            if not branch_file.exists():
                raise ReferenceError(f"Branch does not exist: {branch_name}")

            head_prefix = self.configuration.require(
                "references",
                "head_prefix",
            )

            reference_prefix = self.configuration.require(
                "references",
                "heads_reference_prefix",
            )

            self.repository.head_file.write_text(
                (f"{head_prefix}{reference_prefix}{branch_name}\n"),
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Checked out branch: %s",
                branch_name,
            )

        except OSError as exc:
            LOGGER.exception("Unable to checkout branch.")

            raise ReferenceError(f"Unable to checkout branch: {branch_name}") from exc

    def list_branches(self) -> list[str]:
        """List local branches."""

        try:
            heads_directory = self.repository.heads_directory

            if not heads_directory.exists():
                return []

            return sorted(
                path.name for path in heads_directory.iterdir() if path.is_file()
            )

        except OSError as exc:
            LOGGER.exception("Unable to list branches.")

            raise ReferenceError("Unable to list branches.") from exc

    def create_branch(
        self,
        branch_name: str,
        commit_id: str | None,
    ) -> None:
        """Create a branch reference."""

        if not branch_name:
            raise ReferenceError("Branch name cannot be empty.")

        branch_file = self.repository.heads_directory / branch_name

        if branch_file.exists():
            raise ReferenceError(f"Branch already exists: {branch_name}")

        try:
            branch_file.write_text(
                commit_id or "",
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Created branch '%s' at commit '%s'.",
                branch_name,
                commit_id or "",
            )

        except OSError as exc:
            LOGGER.exception("Unable to create branch.")

            raise ReferenceError("Unable to create branch.") from exc

    def create_tag(
        self,
        tag_name: str,
        commit_id: str | None,
    ) -> None:
        """Create a lightweight tag."""

        if not tag_name:
            raise ReferenceError("Tag name cannot be empty.")

        tag_file = self.repository.tags_directory / tag_name

        if tag_file.exists():
            raise ReferenceError(f"Tag already exists: {tag_name}")

        try:
            tag_file.write_text(
                commit_id or "",
                encoding=UTF8_ENCODING,
            )

            LOGGER.info(
                "Created tag '%s' at commit '%s'.",
                tag_name,
                commit_id or "",
            )

        except OSError as exc:
            LOGGER.exception("Unable to create tag.")

            raise ReferenceError("Unable to create tag.") from exc

    def list_tags(self) -> list[str]:
        """List tags."""

        try:
            tags_directory = self.repository.tags_directory

            if not tags_directory.exists():
                return []

            return sorted(
                path.name for path in tags_directory.iterdir() if path.is_file()
            )

        except OSError as exc:
            LOGGER.exception("Unable to list tags.")

            raise ReferenceError("Unable to list tags.") from exc
