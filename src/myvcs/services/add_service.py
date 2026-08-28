"""File staging service."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.common.application_logging import get_logger
from myvcs.objects.blob_object import BlobObject
from myvcs.repository.object_store import ObjectStore
from myvcs.staging.staging_index import StagingIndex


LOGGER = get_logger(__name__)


class AddService:
    """Stages working-directory files."""

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

        self.staging_index = StagingIndex(
            repository.index_file,
            configuration,
        )

    def add(
        self,
        file_path: str,
    ) -> str:
        """Stage a file."""

        try:
            source_path = (
                self.repository.working_directory
                / file_path
            ).resolve()

            if not source_path.is_file():
                raise RepositoryError(
                    f"File does not exist: {file_path}"
                )

            relative_path = (
                self.repository.relative_path(
                    source_path
                )
            )

            data = source_path.read_bytes()

            blob = BlobObject(
                data=data,
                configuration=self.configuration,
            )

            object_id = self.object_store.write(
                blob
            )

            self.staging_index.add(
                relative_path=relative_path,
                object_id=object_id,
            )

            LOGGER.info(
                "Successfully staged: %s",
                relative_path,
            )

            return object_id

        except RepositoryError:
            raise

        except OSError as exc:
            LOGGER.exception(
                "Unable to stage file."
            )

            raise RepositoryError(
                f"Unable to stage file: {file_path}"
            ) from exc