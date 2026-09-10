"""Garbage collection service tests."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.blob_object import BlobObject
from myvcs.repository.object_store import ObjectStore
from myvcs.services.garbage_collection_service import GarbageCollectionService


def create_configuration() -> ApplicationConfig:
    """Create test configuration."""

    return ApplicationConfig(
        {
            "objects": {
                "hash_algorithm": "sha256",
                "blob_type": "blob",
                "tree_type": "tree",
                "commit_type": "commit",
            },
            "gc": {
                "grace_period_days": 30,
            },
        }
    )


def create_repository(
    tmp_path: Path,
):
    """Create a minimal repository for GC tests."""

    repository = type("Repository", (), {})()

    repository.objects_directory = tmp_path / "objects"
    repository.references_directory = tmp_path / "refs"

    repository.objects_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    repository.references_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return repository


def write_blob(
    repository,
    configuration: ApplicationConfig,
    data: bytes,
) -> str:
    """Write a blob object and return its ID."""

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    blob = BlobObject(
        data=data,
        configuration=configuration,
    )

    return object_store.write(blob)


def object_path(
    repository,
    object_id: str,
) -> Path:
    """Return the loose object path."""

    return (
        repository.objects_directory
        / object_id[:2]
        / object_id[2:]
    )


def create_branch_reference(
    repository,
    commit_id: str,
) -> None:
    """Create a branch reference."""

    heads_directory = repository.references_directory / "heads"

    heads_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (heads_directory / "main").write_text(
        commit_id,
        encoding="utf-8",
    )


def test_reachable_object_is_preserved(
    tmp_path: Path,
):
    """Reachable objects should not be removed."""

    configuration = create_configuration()

    repository = create_repository(tmp_path)

    object_id = write_blob(
        repository,
        configuration,
        b"reachable object",
    )

    create_branch_reference(
        repository,
        object_id,
    )

    service = GarbageCollectionService(
        repository,
        configuration,
    )

    removed = service.collect()

    assert removed == 0

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    assert object_store.exists(object_id)


def test_old_unreachable_object_is_removed(
    tmp_path: Path,
):
    """Old unreachable objects should be removed."""

    configuration = create_configuration()

    repository = create_repository(tmp_path)

    object_id = write_blob(
        repository,
        configuration,
        b"old unreachable object",
    )

    object_file = object_path(
        repository,
        object_id,
    )

    old_timestamp = (
        datetime.now(UTC) - timedelta(days=31)
    ).timestamp()

    os.utime(
        object_file,
        (old_timestamp, old_timestamp),
    )

    service = GarbageCollectionService(
        repository,
        configuration,
    )

    removed = service.collect()

    assert removed == 1
    assert not object_file.exists()


def test_recent_unreachable_object_is_preserved(
    tmp_path: Path,
):
    """Recent unreachable objects should respect the grace period."""

    configuration = create_configuration()

    repository = create_repository(tmp_path)

    object_id = write_blob(
        repository,
        configuration,
        b"recent unreachable object",
    )

    object_file = object_path(
        repository,
        object_id,
    )

    recent_timestamp = (
        datetime.now(UTC) - timedelta(days=1)
    ).timestamp()

    os.utime(
        object_file,
        (recent_timestamp, recent_timestamp),
    )

    service = GarbageCollectionService(
        repository,
        configuration,
    )

    removed = service.collect()

    assert removed == 0
    assert object_file.exists()


def test_mixed_reachable_and_unreachable_objects(
    tmp_path: Path,
):
    """GC should preserve reachable and remove old unreachable objects."""

    configuration = create_configuration()

    repository = create_repository(tmp_path)

    reachable_id = write_blob(
        repository,
        configuration,
        b"reachable",
    )

    unreachable_id = write_blob(
        repository,
        configuration,
        b"unreachable",
    )

    create_branch_reference(
        repository,
        reachable_id,
    )

    unreachable_file = object_path(
        repository,
        unreachable_id,
    )

    old_timestamp = (
        datetime.now(UTC) - timedelta(days=31)
    ).timestamp()

    os.utime(
        unreachable_file,
        (old_timestamp, old_timestamp),
    )

    service = GarbageCollectionService(
        repository,
        configuration,
    )

    removed = service.collect()

    assert removed == 1

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    assert object_store.exists(reachable_id)
    assert not unreachable_file.exists()