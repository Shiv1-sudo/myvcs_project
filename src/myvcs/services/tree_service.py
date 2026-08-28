"""Recursive tree creation service."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import ObjectError
from myvcs.common.application_logging import get_logger
from myvcs.objects.blob_object import BlobObject
from myvcs.objects.tree_object import TreeEntry, TreeObject
from myvcs.repository.object_store import ObjectStore


LOGGER = get_logger(__name__)


class TreeService:
    """Build recursive tree objects."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.object_store = ObjectStore(
            repository.objects_directory,
            configuration,
        )

    def build_tree(
        self,
        entries: dict[str, str],
    ) -> str:
        """Build recursive tree structure."""

        try:
            root: dict = {}

            for relative_path, object_id in entries.items():
                parts = Path(relative_path).parts

                current = root

                for part in parts[:-1]:
                    current = current.setdefault(
                        part,
                        {},
                    )

                current[parts[-1]] = object_id

            return self._write_tree(root)

        except Exception as exc:
            LOGGER.exception(
                "Unable to build recursive tree."
            )

            raise ObjectError(
                "Unable to build recursive tree."
            ) from exc

    def _write_tree(
        self,
        directory: dict,
    ) -> str:
        """Recursively write trees."""

        entries: list[TreeEntry] = []

        blob_type = self.configuration.require(
            "objects",
            "blob_type",
        )

        tree_type = self.configuration.require(
            "objects",
            "tree_type",
        )

        for name, value in sorted(
            directory.items()
        ):
            if isinstance(value, dict):
                child_id = self._write_tree(value)

                entries.append(
                    TreeEntry(
                        name=name,
                        object_id=child_id,
                        object_type=tree_type,
                    )
                )

            else:
                entries.append(
                    TreeEntry(
                        name=name,
                        object_id=value,
                        object_type=blob_type,
                    )
                )

        tree = TreeObject(
            entries=entries,
            configuration=self.configuration,
        )

        return self.object_store.write(tree)