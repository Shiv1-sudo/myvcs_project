"""Checkout service."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import ReferenceError
from myvcs.common.application_logging import get_logger
from myvcs.objects.tree_object import TreeObject
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore
from myvcs.staging.staging_index import StagingIndex

LOGGER = get_logger(__name__)


class CheckoutService:
    """Switch branches and restore working tree."""

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

        self.object_store = ObjectStore(
            repository.objects_directory,
            configuration,
        )

        self.staging_index = StagingIndex(
            repository.index_file,
            configuration,
        )

    def checkout(
        self,
        branch_name: str,
    ) -> None:
        """Checkout branch."""

        try:
            current_branch = self.reference_manager.current_branch()

            if current_branch == branch_name:
                LOGGER.info(
                    "Already on branch: %s",
                    branch_name,
                )
                return

            commit_id = self.reference_manager.get_branch_commit(branch_name)

            if commit_id is None:
                raise ReferenceError(f"Branch not found: {branch_name}")

            commit_data = self.object_store.read(commit_id)

            tree_id = self._get_tree_id(commit_data)

            self._restore_tree(tree_id)

            self.reference_manager.checkout_branch(branch_name)

            self.staging_index.clear()

            LOGGER.info(
                "Checked out branch: %s",
                branch_name,
            )

        except ReferenceError:
            raise

        except Exception as exc:
            LOGGER.exception("Checkout failed.")

            raise ReferenceError("Unable to checkout branch.") from exc

    def _get_tree_id(
        self,
        commit_data: bytes,
    ) -> str:
        """Extract the tree ID from a serialized commit."""

        if not isinstance(commit_data, bytes):
            raise TypeError("Invalid commit data.")

        # VCSObject.serialize() format:
        #
        #     <object_type> <size>\0<payload>
        #
        separator = b"\0"

        if separator in commit_data:
            _, payload = commit_data.split(
                separator,
                1,
            )
        else:
            # Support raw payloads as a fallback.
            payload = commit_data

        text = payload.decode(
            "utf-8",
            errors="replace",
        )

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("tree "):
                tree_id = line[5:].strip()

                if tree_id:
                    return tree_id

        raise ValueError("Commit does not contain a tree.")

    def _read_tree(
        self,
        tree_id: str,
    ) -> TreeObject:
        """Read and deserialize a tree object."""

        tree_data = self.object_store.read(tree_id)

        if not isinstance(tree_data, bytes):
            raise TypeError("Invalid tree data.")

        tree_payload = self._extract_payload(tree_data)

        return TreeObject.deserialize(
            tree_payload,
            self.configuration,
        )

    def _restore_tree(
        self,
        tree_id: str,
        prefix: str = "",
    ) -> None:
        """Restore a tree recursively."""

        tree = self._read_tree(tree_id)

        tree_type = self.configuration.require(
            "objects",
            "tree_type",
        )

        for entry in tree.entries:
            relative_path = Path(prefix) / entry.name

            destination = self.repository.working_directory / relative_path

            if entry.object_type == tree_type:
                destination.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                self._restore_tree(
                    entry.object_id,
                    str(relative_path),
                )

            else:
                blob_data = self.object_store.read(entry.object_id)

                if not isinstance(
                    blob_data,
                    bytes,
                ):
                    raise ValueError("Invalid blob data.")

                blob_payload = self._extract_payload(blob_data)

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                destination.write_bytes(blob_payload)

    def _extract_payload(
        self,
        object_data: bytes,
    ) -> bytes:
        """Remove the VCS object header."""

        if not isinstance(
            object_data,
            bytes,
        ):
            raise TypeError("Invalid object data.")

        separator = b"\0"

        if separator in object_data:
            _, payload = object_data.split(
                separator,
                1,
            )

            return payload

        return object_data
