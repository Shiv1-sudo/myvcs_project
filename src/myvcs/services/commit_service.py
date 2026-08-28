#Index
#  ↓
#Tree
#  ↓
#Commit
# ↓
#HEAD"""Commit creation service."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import CommitError
from myvcs.common.application_logging import get_logger
from myvcs.objects.commit_object import CommitObject
from myvcs.objects.tree_object import TreeObject
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore
from myvcs.staging.staging_index import StagingIndex


LOGGER = get_logger(__name__)


class CommitService:
    """Creates commits from the staging index."""

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

        self.reference_manager = (
            ReferenceManager(
                repository,
                configuration,
            )
        )

    def commit(
        self,
        message: str,
        author: str,
    ) -> str:
        """Create a commit."""

        try:
            entries = (
                self.staging_index.load()
            )

            if not entries:
                raise CommitError(
                    "Nothing to commit."
                )

            tree = TreeObject(
                entries=entries,
                configuration=self.configuration,
            )

            tree_id = self.object_store.write(
                tree
            )

            parent_id = (
                self.reference_manager
                .get_head_commit()
            )

            commit = CommitObject(
                tree_id=tree_id,
                parent_id=parent_id,
                message=message,
                author=author,
                configuration=self.configuration,
            )

            commit_id = (
                self.object_store.write(
                    commit
                )
            )

            self.reference_manager.update_head(
                commit_id
            )
            #adding new value 
            self.staging_index.clear()
            
            LOGGER.info(
                "Commit created successfully: %s",
                commit_id,
            )

            return commit_id

        except CommitError:
            raise

        except Exception as exc:
            LOGGER.exception(
                "Commit creation failed."
            )

            raise CommitError(
                "Unable to create commit."
            ) from exc