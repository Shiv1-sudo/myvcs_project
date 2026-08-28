"""Blob object implementation."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.vcs_object import VCSObject


class BlobObject(VCSObject):
    """Represents file contents."""

    def __init__(
        self,
        data: bytes,
        configuration: ApplicationConfig,
    ):
        object_type = configuration.require(
            "objects",
            "blob_type",
        )

        super().__init__(
            object_type=object_type,
            data=data,
            configuration=configuration,
        )
