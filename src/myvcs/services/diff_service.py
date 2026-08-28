"""Working-tree diff service."""

import difflib
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.objects.tree_object import TreeObject
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore


LOGGER = get_logger(__name__)


class DiffService:
    """Compare HEAD content with working-tree content."""

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

    def diff(self) -> str:
        """Generate working-tree diff."""

        try:
            head_commit_id = (
                self.reference_manager.get_head_commit()
            )

            if not head_commit_id:
                LOGGER.info(
                    "No commits exist; no diff available."
                )
                return ""

            # ObjectStore.read() returns raw serialized bytes.
            commit_data = self.object_store.read(
                head_commit_id
            )

            tree_id = self._get_tree_id(
                commit_data
            )

            head_files = self._flatten_tree(
                tree_id
            )

            working_files = self._working_files()

            output: list[str] = []

            all_paths = sorted(
                set(head_files) | working_files
            )

            for relative_path in all_paths:
                head_object_id = head_files.get(
                    relative_path
                )

                file_path = (
                    self.repository.working_directory
                    / Path(relative_path)
                )

                # File existed in HEAD but has been deleted.
                if (
                    head_object_id is not None
                    and relative_path not in working_files
                ):
                    output.append(
                        f"deleted: {relative_path}"
                    )
                    continue

                # File does not exist in HEAD.
                if head_object_id is None:
                    output.append(
                        f"added: {relative_path}"
                    )
                    continue

                # File exists in both HEAD and working tree.
                try:
                    old_blob_data = (
                        self.object_store.read(
                            head_object_id
                        )
                    )
                except Exception:
                    LOGGER.exception(
                        "Unable to read blob: %s",
                        head_object_id,
                    )
                    raise

                old_blob_text = (
                    self._extract_object_payload(
                        old_blob_data
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )
                )

                new_text = file_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )

                if old_blob_text == new_text:
                    continue

                diff_lines = difflib.unified_diff(
                    old_blob_text.splitlines(),
                    new_text.splitlines(),
                    fromfile=f"a/{relative_path}",
                    tofile=f"b/{relative_path}",
                    lineterm="",
                )

                output.extend(diff_lines)

            LOGGER.info(
                "Diff generated. Files=%d",
                len(all_paths),
            )

            return "\n".join(output)

        except Exception:
            LOGGER.exception(
                "Unable to generate working-tree diff."
            )
            raise

    def _get_tree_id(
        self,
        commit_data: bytes,
    ) -> str:
        """Extract the tree ID from a serialized commit."""

        if not isinstance(commit_data, bytes):
            raise ValueError(
                "Invalid commit data."
            )

        # VCSObject.serialize() format:
        #
        #     <object_type> <size>\0<payload>
        #
        # Remove the VCS object header first.
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

        raise ValueError(
            "Commit does not contain a tree."
        )

    def _extract_object_payload(
        self,
        object_data: bytes,
    ) -> bytes:
        """Extract payload from serialized VCS object data."""

        if not isinstance(object_data, bytes):
            raise ValueError(
                "Invalid VCS object data."
            )

        separator = b"\0"

        if separator in object_data:
            _, payload = object_data.split(
                separator,
                1,
            )
            return payload

        # Fallback for raw object payloads.
        return object_data

    def _working_files(self) -> set[str]:
        """Find files in the working tree."""

        result: set[str] = set()

        metadata_directory = (
            self.repository.metadata_directory
        )

        for path in (
            self.repository.working_directory.rglob("*")
        ):
            if not path.is_file():
                continue

            # Never include MyVCS metadata.
            if metadata_directory in path.parents:
                continue

            relative = self.repository.relative_path(
                path
            )

            result.add(
                relative.replace(
                    "\\",
                    "/",
                )
            )

        return result

    def _flatten_tree(
        self,
        tree_id: str,
        prefix: str = "",
    ) -> dict[str, str]:
        """Flatten a recursive tree into file paths."""

        tree_data = self.object_store.read(
            tree_id
        )

        # ObjectStore.read() returns serialized bytes.
        # Remove the VCS object header before deserializing.
        tree_payload = self._extract_object_payload(
            tree_data
        )

        tree = TreeObject.deserialize(
            tree_payload,
            self.configuration,
        )

        result: dict[str, str] = {}

        tree_type = self.configuration.require(
            "objects",
            "tree_type",
        )

        for entry in tree.entries:
            if prefix:
                path = (
                    Path(prefix)
                    / entry.name
                )
            else:
                path = Path(entry.name)

            relative_path = str(path).replace(
                "\\",
                "/",
            )

            if entry.object_type == tree_type:
                result.update(
                    self._flatten_tree(
                        entry.object_id,
                        relative_path,
                    )
                )
            else:
                result[relative_path] = (
                    entry.object_id
                )

        return result