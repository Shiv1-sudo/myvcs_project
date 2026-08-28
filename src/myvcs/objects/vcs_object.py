# <object type> <content length>\0<content>
"""Base VCS object."""

import hashlib

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import (
    ObjectSerializationError,
)
from myvcs.common.application_logging import get_logger

LOGGER = get_logger(__name__)


class VCSObject:
    """Base class for content-addressable VCS objects."""

    def __init__(
        self,
        object_type: str,
        data: bytes,
        configuration: ApplicationConfig,
    ):
        self.object_type = object_type
        self.data = data
        self.configuration = configuration

    def serialize(self) -> bytes:
        """Serialize object using Git-like object format."""

        try:
            header = (f"{self.object_type} {len(self.data)}\0").encode()

            return header + self.data

        except Exception as exc:
            LOGGER.exception("Object serialization failed.")

            raise ObjectSerializationError("Unable to serialize VCS object.") from exc

    def object_id(self) -> str:
        """Calculate content-addressable object ID."""

        try:
            algorithm_name = self.configuration.require(
                "objects",
                "hash_algorithm",
            )

            hasher = hashlib.new(algorithm_name)

            hasher.update(self.serialize())

            object_id = hasher.hexdigest()

            LOGGER.debug(
                "Generated object ID: %s",
                object_id,
            )

            return object_id

        except Exception as exc:
            LOGGER.exception("Object ID generation failed.")

            raise ObjectSerializationError("Unable to generate object ID.") from exc
