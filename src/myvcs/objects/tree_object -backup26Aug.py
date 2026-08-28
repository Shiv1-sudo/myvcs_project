"""Tree object implementation."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.vcs_object import VCSObject


class TreeObject(VCSObject):
    """Represents a directory tree."""

    def __init__(
        self,
        entries: dict[str, str],
        configuration: ApplicationConfig,
    ):
        tree_lines = [
            f"{path} {object_id}"
            for path, object_id in sorted(
                entries.items()
            )
        ]

        data = "\n".join(
            tree_lines
        ).encode("utf-8")

        object_type = configuration.require(
            "objects",
            "tree_type",
        )

        super().__init__(
            object_type=object_type,
            data=data,
            configuration=configuration,
        )