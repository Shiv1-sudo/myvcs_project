"""Object reachability analysis."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.objects.commit_object import CommitObject
from myvcs.objects.tree_object import TreeObject
from myvcs.repository.object_store import ObjectStore

LOGGER = get_logger(__name__)


class ReachabilityAnalyzer:
    """Find objects reachable from references."""

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

    def find_reachable_objects(self) -> set[str]:
        """Return all reachable object IDs."""

        reachable: set[str] = set()

        references = self._reference_ids()

        for object_id in references:
            self._visit(
                object_id,
                reachable,
            )

        LOGGER.info(
            "Reachability analysis completed. Objects=%d",
            len(reachable),
        )

        return reachable

    def _reference_ids(self) -> list[str]:
        """Get IDs from branches and tags."""

        references = []

        for directory_name in (
            "heads",
            "tags",
        ):
            directory = self.repository.references_directory / directory_name

            if not directory.exists():
                continue

            for path in directory.iterdir():
                if path.is_file():
                    value = path.read_text(encoding="utf-8").strip()

                    if value:
                        references.append(value)

        return references

    def _visit(
        self,
        object_id: str,
        reachable: set[str],
    ) -> None:
        """Recursively visit object graph."""

        if not object_id:
            return

        if object_id in reachable:
            return

        reachable.add(object_id)

        obj_data = self.object_store.read(object_id)
        if not isinstance(obj_data, bytes):
            raise TypeError(f"Invalid object data for ID: {object_id}")

        separator = b"\0"

        if separator in obj_data:
            header, payload = obj_data.split(
                separator,
                1,
            )
        else:
            header = obj_data
            payload = obj_data

        object_type = header.split(
            b" ",
            1,
                )[0].decode("utf-8")

        tree_type = self.configuration.require(
            "objects",
            "tree_type",
        )

        commit_type = self.configuration.require(
            "objects",
            "commit_type",
        )

        if object_type == commit_type:
            obj = CommitObject.deserialize(
                payload,
                self.configuration,
                            )
            self._visit(
                obj.tree_id,
                reachable,
            )

            if obj.parent_id:
                self._visit(
                    obj.parent_id,
                    reachable,
                )

        elif object_type == tree_type:
            obj = TreeObject.deserialize(
                payload,
                self.configuration,
               )
            for entry in obj.entries:
                self._visit(
                    entry.object_id,
                    reachable,
                )
