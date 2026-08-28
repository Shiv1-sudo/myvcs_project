"""Repository status service."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.objects.blob_object import BlobObject
from myvcs.repository.object_store import ObjectStore
from myvcs.references.reference_manager import ReferenceManager
from myvcs.staging.staging_index import StagingIndex


LOGGER = get_logger(__name__)


class StatusService:
    """Calculate working-tree status."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.staging_index = StagingIndex(
            repository.index_file,
            configuration,
        )

        self.object_store = ObjectStore(
            repository.objects_directory,
            configuration,
        )

        self.reference_manager = ReferenceManager(
            repository,
            configuration,
        )

    def _working_files(self) -> set[str]:
        """Find files in the working tree."""

        result: set[str] = set()

        metadata_directory = (
            self.repository.metadata_directory
        )

        excluded_directories = {
            ".pytest_cache",
            "__pycache__",
        }

        for path in (
            self.repository.working_directory.rglob("*")
        ):
            if not path.is_file():
                continue

            if metadata_directory in path.parents:
                continue

            if any(
                directory.name in excluded_directories
                for directory in path.parents
            ):
                continue

            relative_path = (
                self.repository.relative_path(path)
            )

            relative_path = relative_path.replace(
                "\\",
                "/",
            )

            result.add(relative_path)

        return result

    def _working_blob_id(
        self,
        relative_path: str,
    ) -> str:
        """Calculate the blob ID for a working-tree file."""

        file_path = (
            self.repository.working_directory
            / Path(relative_path)
        )

        data = file_path.read_bytes()

        blob = BlobObject(
            data=data,
            configuration=self.configuration,
        )

        return blob.object_id()

    def _read_object_data(
        self,
        object_id: str,
    ) -> bytes:
        """Read raw object data."""

        return self.object_store.read(
            object_id
        )

    def _strip_object_header(
        self,
        data: bytes,
    ) -> bytes:
        """Remove the VCS object header."""

        if b"\x00" not in data:
            return data

        return data.split(
            b"\x00",
            1,
        )[1]

    def _read_commit(
        self,
        commit_id: str,
    ) -> dict[str, str | None]:
        """Read commit metadata from a stored object."""

        raw = self._read_object_data(
            commit_id
        )

        payload = self._strip_object_header(
            raw
        )

        text = payload.decode(
            "utf-8",
            errors="replace",
        )

        tree_id: str | None = None
        parent_id: str | None = None

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("tree "):
                tree_id = line.removeprefix(
                    "tree "
                ).strip()

            elif line.startswith("parent "):
                parent_id = line.removeprefix(
                    "parent "
                ).strip()

        if not tree_id:
            raise ValueError(
                f"Commit {commit_id} does not contain a tree."
            )

        return {
            "tree_id": tree_id,
            "parent_id": parent_id,
        }

    def _read_tree_entries(
        self,
        tree_id: str,
        prefix: str = "",
    ) -> dict[str, str]:
        """Read a tree recursively."""

        raw = self._read_object_data(
            tree_id
        )

        payload = self._strip_object_header(
            raw
        )

        text = payload.decode(
            "utf-8",
            errors="replace",
        )

        result: dict[str, str] = {}

        if not text:
            return result

        tree_type = self.configuration.require(
            "objects",
            "tree_type",
        )

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            parts = line.split(
                " ",
                2,
            )

            if len(parts) != 3:
                continue

            # TreeObject serializes entries as:
            #
            # name object_id object_type
            #
            # Example:
            # feature.txt abc123... blob
            #
            name, object_id, object_type = parts

            relative_path = (
                Path(prefix) / name
                if prefix
                else Path(name)
            )

            relative_path = (
                relative_path.as_posix()
            )

            if object_type == tree_type:
                result.update(
                    self._read_tree_entries(
                        object_id,
                        relative_path,
                    )
                )
            else:
                result[relative_path] = object_id

        return result

    def _head_files(self) -> dict[str, str]:
        """Return files represented by HEAD."""

        head_commit_id = (
            self.reference_manager.get_head_commit()
        )

        if not head_commit_id:
            return {}

        commit = self._read_commit(
            head_commit_id
        )

        tree_id = commit["tree_id"]

        if not tree_id:
            return {}

        return self._read_tree_entries(
            tree_id
        )

    def get_status(self) -> dict[str, list[str]]:
        """Calculate repository status."""

        try:
            staged = self.staging_index.load()

            working_files = self._working_files()
            working_set = set(working_files)

            staged_files = set(staged)

            head_files = self._head_files()
            head_set = set(head_files)

            # -------------------------------------------------
            # STAGED CHANGES
            #
            # Compare the staging index against HEAD.
            # -------------------------------------------------

            staged_changes: set[str] = set()

            for relative_path in staged_files:
                staged_id = staged[
                    relative_path
                ]

                head_id = head_files.get(
                    relative_path
                )

                if staged_id != head_id:
                    staged_changes.add(
                        relative_path
                    )

            # -------------------------------------------------
            # ADDED
            #
            # Files staged that do not exist in HEAD.
            # -------------------------------------------------

            added = sorted(
                staged_files - head_set
            )

            # -------------------------------------------------
            # WORKING-TREE MODIFICATIONS
            #
            # 1. Staged files changed after staging.
            # 2. HEAD files changed without being staged.
            # -------------------------------------------------

            modified: set[str] = set()

            # Files that are staged and then changed again.
            for relative_path in (
                working_set & staged_files
            ):
                current_id = (
                    self._working_blob_id(
                        relative_path
                    )
                )

                staged_id = staged[
                    relative_path
                ]

                if current_id != staged_id:
                    modified.add(
                        relative_path
                    )

            # Files tracked by HEAD but not staged,
            # whose working-tree content differs from HEAD.
            for relative_path in (
                working_set & head_set
            ):
                if relative_path in staged_files:
                    continue

                current_id = (
                    self._working_blob_id(
                        relative_path
                    )
                )

                head_id = head_files[
                    relative_path
                ]

                if current_id != head_id:
                    modified.add(
                        relative_path
                    )

            # -------------------------------------------------
            # DELETED
            #
            # Files tracked by HEAD that are no longer
            # present in the working tree.
            # -------------------------------------------------

            deleted = sorted(
                head_set - working_set
            )

            # -------------------------------------------------
            # UNTRACKED
            #
            # A file is untracked only when it exists in the
            # working tree, is not in HEAD, and is not staged.
            # -------------------------------------------------

            untracked = sorted(
                working_set
                - head_set
                - staged_files
            )

            result = {
                "staged": sorted(
                    staged_changes
                ),
                "added": added,
                "modified": sorted(
                    modified
                ),
                "deleted": deleted,
                "untracked": untracked,
            }

            LOGGER.info(
                "Status calculated. "
                "Staged=%d Added=%d Modified=%d "
                "Deleted=%d Untracked=%d",
                len(result["staged"]),
                len(result["added"]),
                len(result["modified"]),
                len(result["deleted"]),
                len(result["untracked"]),
            )

            return result

        except Exception:
            LOGGER.exception(
                "Unable to calculate repository status."
            )
            raise