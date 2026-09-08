"""Commit object implementation."""

from datetime import UTC, datetime

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import ObjectError
from myvcs.common.application_logging import get_logger
from myvcs.objects.vcs_object import VCSObject

LOGGER = get_logger(__name__)


class CommitObject(VCSObject):
    """Represents a commit."""

    def __init__(
        self,
        tree_id: str,
        parent_id: str | None,
        message: str,
        author: str,
        configuration: ApplicationConfig,
    ):
        lines = [
            f"tree {tree_id}",
        ]

        if parent_id:
            lines.append(f"parent {parent_id}")

        timestamp = datetime.now(UTC).isoformat()

        lines.extend(
            [
                f"author {author}",
                f"timestamp {timestamp}",
                "",
                message,
            ]
        )

        data = "\n".join(lines).encode("utf-8")

        object_type = configuration.require(
            "objects",
            "commit_type",
        )

        super().__init__(
            object_type=object_type,
            data=data,
            configuration=configuration,
        )

    @classmethod
    def deserialize(
        cls,
        data: bytes,
        configuration: ApplicationConfig,
    ) -> "CommitObject":
        """Deserialize a commit payload."""

        try:
            if not isinstance(data, bytes):
                raise TypeError("Invalid commit data.")

            separator = b"\0"

            if separator in data:
                _, payload = data.split(
                    separator,
                    1,
                )
            else:
                payload = data

            text = payload.decode(
                "utf-8",
                errors="replace",
            )

            tree_id: str | None = None
            parent_id: str | None = None
            author: str | None = None
            timestamp: str | None = None
            message_lines: list[str] = []

            in_message = False

            for line in text.splitlines():
                if in_message:
                    message_lines.append(line)
                    continue

                if not line.strip():
                    in_message = True
                    continue

                if line.startswith("tree "):
                    tree_id = line[5:].strip()

                elif line.startswith("parent "):
                    parent_id = line[7:].strip()

                elif line.startswith("author "):
                    author = line[7:].strip()

                elif line.startswith("timestamp "):
                    timestamp = line[10:].strip()

                else:
                    raise ObjectError(
                        f"Invalid commit metadata: {line}"
                    )

            if not tree_id:
                raise ObjectError(
                    "Commit tree ID cannot be empty."
                )

            if author is None:
                raise ObjectError(
                    "Commit author cannot be empty."
                )

            if timestamp is None:
                raise ObjectError(
                    "Commit timestamp cannot be empty."
                )

            message = "\n".join(message_lines)

            commit = cls(
                tree_id=tree_id,
                parent_id=parent_id,
                message=message,
                author=author,
                configuration=configuration,
            )

            return commit

        except ObjectError:
            raise

        except Exception as exc:
            LOGGER.exception(
                "Unable to deserialize commit object."
            )

            raise ObjectError(
                "Unable to deserialize commit object."
            ) from exc