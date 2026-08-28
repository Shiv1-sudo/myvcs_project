"""Tree object implementation."""

from dataclasses import dataclass

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import ObjectError
from myvcs.common.application_logging import get_logger
from myvcs.objects.vcs_object import VCSObject


LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class TreeEntry:
    """Entry inside a tree."""

    name: str
    object_id: str
    object_type: str


class TreeObject(VCSObject):
    """Represents a directory tree."""

    def __init__(
        self,
        entries: dict[str, str] | list[TreeEntry],
        configuration: ApplicationConfig,
    ):
        self.configuration = configuration

        if isinstance(entries, dict):
            self.entries = [
                TreeEntry(
                    name=path,
                    object_id=object_id,
                    object_type=configuration.require(
                        "objects",
                        "blob_type",
                    ),
                )
                for path, object_id in entries.items()
            ]
        else:
            self.entries = list(entries)

        data = self._serialize_entries()

        super().__init__(
            object_type=configuration.require(
                "objects",
                "tree_type",
            ),
            data=data,
            configuration=configuration,
        )

    def _serialize_entries(self) -> bytes:
        """Serialize tree entries without the VCS object header."""

        try:
            lines: list[str] = []

            for entry in sorted(
                self.entries,
                key=lambda item: item.name,
            ):
                lines.append(
                    f"{entry.name} "
                    f"{entry.object_id} "
                    f"{entry.object_type}"
                )

            return "\n".join(lines).encode("utf-8")

        except Exception as exc:
            LOGGER.exception(
                "Unable to serialize tree entries."
            )

            raise ObjectError(
                "Unable to serialize tree entries."
            ) from exc

    def serialize(self) -> bytes:
        """Serialize the complete tree object."""

        try:
            return super().serialize()

        except Exception as exc:
            LOGGER.exception(
                "Unable to serialize tree object."
            )

            raise ObjectError(
                "Unable to serialize tree object."
            ) from exc

    @classmethod
    def deserialize(
        cls,
        data: bytes,
        configuration: ApplicationConfig,
    ) -> "TreeObject":
        """Deserialize tree entry data."""

        try:
            entries: list[TreeEntry] = []

            text = data.decode(
                "utf-8",
                errors="replace",
            )

            for line in text.splitlines():
                line = line.strip()

                if not line:
                    continue

                parts = line.split(
                    " ",
                    maxsplit=2,
                )

                if len(parts) != 3:
                    raise ObjectError(
                        f"Invalid tree entry: {line}"
                    )

                name, object_id, object_type = parts

                if not name:
                    raise ObjectError(
                        "Tree entry name cannot be empty."
                    )

                if not object_id:
                    raise ObjectError(
                        "Tree entry object ID cannot be empty."
                    )

                if not object_type:
                    raise ObjectError(
                        "Tree entry object type cannot be empty."
                    )

                entries.append(
                    TreeEntry(
                        name=name,
                        object_id=object_id,
                        object_type=object_type,
                    )
                )

            return cls(
                entries=entries,
                configuration=configuration,
            )

        except ObjectError:
            raise

        except Exception as exc:
            LOGGER.exception(
                "Unable to deserialize tree object."
            )

            raise ObjectError(
                "Unable to deserialize tree object."
            ) from exc