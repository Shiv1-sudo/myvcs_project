"""Commit object implementation."""

from datetime import datetime, timezone

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.vcs_object import VCSObject


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
            lines.append(
                f"parent {parent_id}"
            )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        lines.extend(
            [
                f"author {author}",
                f"timestamp {timestamp}",
                "",
                message,
            ]
        )

        data = "\n".join(
            lines
        ).encode("utf-8")

        object_type = configuration.require(
            "objects",
            "commit_type",
        )

        super().__init__(
            object_type=object_type,
            data=data,
            configuration=configuration,
        )