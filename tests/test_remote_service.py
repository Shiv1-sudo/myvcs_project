"""Remote and clone service tests."""

from pathlib import Path

import pytest

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.objects.blob_object import BlobObject
from myvcs.remote.local_remote import LocalRemote
from myvcs.repository.object_store import ObjectStore
from myvcs.repository.repository_manager import RepositoryManager
from myvcs.services.clone_service import CloneService


def create_configuration() -> ApplicationConfig:
    """Create test configuration."""

    return ApplicationConfig(
        {
            "repository": {
                "metadata_directory": ".myvcs",
                "objects_directory": "objects",
                "references_directory": "refs",
                "heads_directory": "heads",
                "tags_directory": "tags",
                "index_file": "index",
                "head_file": "HEAD",
                "repository_config_file": "config",
            },
            "references": {
                "default_branch": "main",
                "head_prefix": "ref: ",
                "heads_reference_prefix": "refs/heads/",
            },
            "objects": {
                "blob_type": "blob",
                "tree_type": "tree",
                "commit_type": "commit",
                "hash_algorithm": "sha256",
            },
        }
    )


def create_repository(
    path: Path,
) -> tuple[RepositoryManager, ApplicationConfig]:
    """Create an initialized repository."""

    configuration = create_configuration()

    repository = RepositoryManager(
        path,
        configuration,
    )

    repository.initialize()

    return repository, configuration


def create_blob(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    content: bytes,
) -> str:
    """Create and store a blob."""

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    blob = BlobObject(
        content,
        configuration,
    )

    return object_store.write(blob)


def test_push_copies_objects_and_branch_reference(
    tmp_path: Path,
):
    """Push should copy objects and the selected branch reference."""

    source, configuration = create_repository(
        tmp_path / "source",
    )

    remote_repository, _ = create_repository(
        tmp_path / "remote",
    )

    blob_id = create_blob(
        source,
        configuration,
        b"remote content",
    )

    source_branch = source.heads_directory / "main"

    source_branch.write_text(
        blob_id,
        encoding="utf-8",
    )

    remote = LocalRemote(
        remote_repository,
    )

    remote.push(
        source,
        "main",
    )

    remote_object_store = ObjectStore(
        remote_repository.objects_directory,
        configuration,
    )

    assert remote_object_store.exists(blob_id)

    remote_branch = remote_repository.heads_directory / "main"

    assert remote_branch.read_text(
        encoding="utf-8",
    ).strip() == blob_id


def test_fetch_copies_remote_objects(
    tmp_path: Path,
):
    """Fetch should copy objects from the remote repository."""

    remote_repository, configuration = create_repository(
        tmp_path / "remote",
    )

    target_repository, _ = create_repository(
        tmp_path / "target",
    )

    blob_id = create_blob(
        remote_repository,
        configuration,
        b"fetched content",
    )

    remote = LocalRemote(
        remote_repository,
    )

    remote.fetch(
        target_repository,
    )

    target_object_store = ObjectStore(
        target_repository.objects_directory,
        configuration,
    )

    assert target_object_store.exists(blob_id)


def test_clone_initializes_destination_and_fetches_objects(
    tmp_path: Path,
):
    """Clone should initialize the destination and fetch objects."""

    remote_repository, configuration = create_repository(
        tmp_path / "remote",
    )

    blob_id = create_blob(
        remote_repository,
        configuration,
        b"cloned content",
    )

    remote_branch = remote_repository.heads_directory / "main"

    remote_branch.write_text(
        blob_id,
        encoding="utf-8",
    )

    destination_path = tmp_path / "clone"

    clone_service = CloneService(
        configuration,
    )

    clone_service.clone(
        str(remote_repository.working_directory),
        str(destination_path),
    )

    destination = RepositoryManager(
        destination_path,
        configuration,
    )

    object_store = ObjectStore(
        destination.objects_directory,
        configuration,
    )

    assert destination.exists()
    assert object_store.exists(blob_id)


def test_clone_invalid_repository_raises_error(
    tmp_path: Path,
):
    """Clone should reject a source that is not a repository."""

    clone_service = CloneService(
        create_configuration(),
    )

    with pytest.raises(
        RepositoryError,
        match="Unable to clone repository.",
    ):
        clone_service.clone(
            str(tmp_path / "missing"),
            str(tmp_path / "clone"),
        )