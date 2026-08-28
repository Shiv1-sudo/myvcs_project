"""Pack service."""

import uuid

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.repository.object_store import ObjectStore
from myvcs.storage.pack_file import PackFile
from myvcs.storage.reachability import ReachabilityAnalyzer

LOGGER = get_logger(__name__)


class PackService:
    """Pack loose objects."""

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

        self.reachability = ReachabilityAnalyzer(
            repository,
            configuration,
        )

        self.pack_directory = repository.objects_directory / "pack"

    def pack(self) -> None:
        """Pack reachable objects."""

        reachable = self.reachability.find_reachable_objects()

        objects = {}

        for object_id in reachable:
            try:
                obj = self.object_store.read(object_id)

                objects[object_id] = obj.serialize()

            except Exception:
                LOGGER.exception(
                    "Unable to pack object: %s",
                    object_id,
                )

        pack_name = f"pack-{uuid.uuid4().hex}"

        pack_file = PackFile(
            self.pack_directory,
            self.configuration,
        )

        pack_file.create(
            objects,
            pack_name,
        )

        LOGGER.info("Object packing completed.")
