"""Persistent VCS object storage."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_constants import (
    OBJECT_DIRECTORY_PREFIX_LENGTH,
    OBJECT_ID_LENGTH,
)
from myvcs.common.application_exceptions import ObjectStoreError
from myvcs.common.application_logging import get_logger
from myvcs.objects.vcs_object import VCSObject


LOGGER = get_logger(__name__)


class ObjectStore:
    """Reads and writes immutable VCS objects."""

    def __init__(
        self,
        objects_directory: Path,
        configuration: ApplicationConfig,
    ):
        self.objects_directory = objects_directory
        self.configuration = configuration

    def _object_path(
        self,
        object_id: str,
    ) -> Path:
        """Build object path."""

        if len(object_id) != OBJECT_ID_LENGTH:
            raise ObjectStoreError(
                f"Invalid object ID: {object_id}"
            )

        directory_name = object_id[
            :OBJECT_DIRECTORY_PREFIX_LENGTH
        ]

        filename = object_id[
            OBJECT_DIRECTORY_PREFIX_LENGTH:
        ]

        return (
            self.objects_directory
            / directory_name
            / filename
        )

    def exists(
        self,
        object_id: str,
    ) -> bool:
        """Check whether object exists."""

        return self._object_path(
            object_id
        ).is_file()

    def write(
        self,
        vcs_object: VCSObject,
    ) -> str:
        """Persist an object."""

        try:
            serialized_object = (
                vcs_object.serialize()
            )

            object_id = vcs_object.object_id()

            object_path = self._object_path(
                object_id
            )

            object_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if not object_path.exists():
                object_path.write_bytes(
                    serialized_object
                )

                LOGGER.info(
                    "Object created: %s",
                    object_id,
                )
            else:
                LOGGER.debug(
                    "Object already exists: %s",
                    object_id,
                )

            return object_id

        except OSError as exc:
            LOGGER.exception(
                "Failed to write object."
            )

            raise ObjectStoreError(
                f"Unable to write object: {exc}"
            ) from exc

    def read(
        self,
        object_id: str,
    ) -> bytes:
        """Read a raw object."""

        try:
            object_path = self._object_path(
                object_id
            )

            if not object_path.exists():
                raise ObjectStoreError(
                    f"Object not found: {object_id}"
                )

            return object_path.read_bytes()

        except ObjectStoreError:
            raise

        except OSError as exc:
            LOGGER.exception(
                "Failed to read object: %s",
                object_id,
            )

            raise ObjectStoreError(
                f"Unable to read object: {object_id}"
            ) from exc