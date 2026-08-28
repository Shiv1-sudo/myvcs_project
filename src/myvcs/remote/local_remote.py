"""Local filesystem remote."""

import shutil

from myvcs.common.application_logging import get_logger
from myvcs.remote.remote import Remote

LOGGER = get_logger(__name__)


class LocalRemote(Remote):
    """Filesystem-based remote."""

    def __init__(self, remote_repository):
        self.remote_repository = remote_repository

    def push(
        self,
        source_repository,
        branch_name: str,
    ) -> None:
        """Push objects to remote."""

        source_objects = source_repository.objects_directory

        destination_objects = self.remote_repository.objects_directory

        destination_objects.mkdir(
            parents=True,
            exist_ok=True,
        )

        for directory in source_objects.iterdir():
            if not directory.is_dir():
                continue

            target_directory = destination_objects / directory.name

            target_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            for object_file in directory.iterdir():
                target = target_directory / object_file.name

                if not target.exists():
                    shutil.copy2(
                        object_file,
                        target,
                    )

        commit_id = source_repository.references_directory / "heads" / branch_name

        remote_branch = (
            self.remote_repository.references_directory / "heads" / branch_name
        )

        remote_branch.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if commit_id.exists():
            shutil.copy2(
                commit_id,
                remote_branch,
            )

        LOGGER.info(
            "Push completed: %s",
            branch_name,
        )

    def fetch(
        self,
        target_repository,
    ) -> None:
        """Fetch remote objects."""

        source_objects = self.remote_repository.objects_directory

        destination_objects = target_repository.objects_directory

        destination_objects.mkdir(
            parents=True,
            exist_ok=True,
        )

        for directory in source_objects.iterdir():
            if not directory.is_dir():
                continue

            target_directory = destination_objects / directory.name

            target_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            for object_file in directory.iterdir():
                target = target_directory / object_file.name

                if not target.exists():
                    shutil.copy2(
                        object_file,
                        target,
                    )

        LOGGER.info("Fetch completed.")
