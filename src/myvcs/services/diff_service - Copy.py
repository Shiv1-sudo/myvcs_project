"""Diff service."""

import difflib

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.repository.object_store import ObjectStore
from myvcs.staging.staging_index import StagingIndex


LOGGER = get_logger(__name__)


class DiffService:
    """Compare staged content with working content."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.staging_index = StagingIndex(
            repository.index_file,
            configuration,
        )

        self.object_store = ObjectStore(
            repository.objects_directory,
            configuration,
        )

    def diff(self) -> str:
        """Generate working-tree diff."""

        output = []

        entries = self.staging_index.load()

        for relative_path, object_id in sorted(
            entries.items()
        ):
            file_path = (
                self.repository.working_directory
                / relative_path
            )

            if not file_path.exists():
                output.append(
                    f"deleted: {relative_path}"
                )
                continue

            old_blob = self.object_store.read(
                object_id
            )

            old_text = old_blob.data.decode(
                "utf-8",
                errors="replace",
            )

            new_text = file_path.read_text(
                encoding="utf-8"
            )

            if old_text == new_text:
                continue

            diff_lines = difflib.unified_diff(
                old_text.splitlines(),
                new_text.splitlines(),
                fromfile=relative_path,
                tofile=relative_path,
                lineterm="",
            )

            output.extend(diff_lines)

        LOGGER.info(
            "Diff generated. Files=%d",
            len(entries),
        )

        return "\n".join(output)