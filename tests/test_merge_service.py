"""Merge service tests."""

from pathlib import Path

import pytest

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import CommitError
from myvcs.objects.blob_object import BlobObject
from myvcs.objects.commit_object import CommitObject
from myvcs.objects.tree_object import TreeObject
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore
from myvcs.repository.repository_manager import RepositoryManager
from myvcs.services.merge_service import MergeService


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
                "remotes_directory": "remotes",
                "index_file": "index",
                "head_file": "HEAD",
                "repository_config_file": "config",
            },
            "objects": {
                "hash_algorithm": "sha256",
                "blob_type": "blob",
                "tree_type": "tree",
                "commit_type": "commit",
            },
            "references": {
                "head_prefix": "ref: ",
                "heads_reference_prefix": "refs/heads/",
                "tags_reference_prefix": "refs/tags/",
                "remotes_reference_prefix": "refs/remotes/",
                "default_branch": "main",
            },
            "index": {
                "version": 1,
            },
        }
    )


def create_repository(
    tmp_path: Path,
) -> tuple[RepositoryManager, ApplicationConfig]:
    """Create an initialized test repository."""

    configuration = create_configuration()

    repository = RepositoryManager(
        tmp_path,
        configuration,
    )

    repository.initialize()

    return repository, configuration


def create_commit(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    filename: str,
    content: bytes,
    parent_id: str | None = None,
) -> str:
    """Create a commit containing one file."""

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    blob = BlobObject(
        data=content,
        configuration=configuration,
    )

    blob_id = object_store.write(blob)

    tree = TreeObject(
        entries={
            filename: blob_id,
        },
        configuration=configuration,
    )

    tree_id = object_store.write(tree)

    commit = CommitObject(
        tree_id=tree_id,
        parent_id=parent_id,
        message=f"Commit {filename}",
        author="Test Developer",
        configuration=configuration,
    )

    return object_store.write(commit)


def test_fast_forward_merge_updates_head_and_working_tree(
    tmp_path: Path,
):
    """Fast-forward merge should update HEAD and restore the source tree."""

    repository, configuration = create_repository(tmp_path)

    references = ReferenceManager(
        repository,
        configuration,
    )

    base_commit = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"base content",
    )

    references.update_head(base_commit)

    source_commit = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"source content",
        parent_id=base_commit,
    )

    references.create_branch(
        "feature",
        source_commit,
    )

    working_file = repository.working_directory / "hello.txt"
    working_file.write_bytes(b"old working tree")

    merge_service = MergeService(
        repository,
        configuration,
    )

    result = merge_service.merge("feature")

    assert result == source_commit
    assert references.get_head_commit() == source_commit
    assert working_file.read_bytes() == b"source content"


def test_merge_same_commit_is_successful(
    tmp_path: Path,
):
    """Merging a branch already at HEAD should be harmless."""

    repository, configuration = create_repository(tmp_path)

    references = ReferenceManager(
        repository,
        configuration,
    )

    commit_id = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"content",
    )

    references.update_head(commit_id)

    references.create_branch(
        "feature",
        commit_id,
    )

    merge_service = MergeService(
        repository,
        configuration,
    )

    result = merge_service.merge("feature")

    assert result == commit_id
    assert references.get_head_commit() == commit_id


def test_merge_missing_branch_raises_error(
    tmp_path: Path,
):
    """Merging a missing branch should raise CommitError."""

    repository, configuration = create_repository(tmp_path)

    merge_service = MergeService(
        repository,
        configuration,
    )

    with pytest.raises(CommitError):
        merge_service.merge("missing")


def test_non_fast_forward_merge_is_rejected(
    tmp_path: Path,
):
    """Non-fast-forward merges should remain explicitly unsupported."""

    repository, configuration = create_repository(tmp_path)

    references = ReferenceManager(
        repository,
        configuration,
    )

    base_commit = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"base content",
    )

    references.update_head(base_commit)

    current_commit = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"main content",
        parent_id=base_commit,
    )

    references.update_head(current_commit)

    source_commit = create_commit(
        repository,
        configuration,
        "hello.txt",
        b"feature content",
        parent_id=base_commit,
    )

    references.create_branch(
        "feature",
        source_commit,
    )

    merge_service = MergeService(
        repository,
        configuration,
    )

    with pytest.raises(
        CommitError,
        match="Non-fast-forward merge is not implemented yet.",
    ):
        merge_service.merge("feature")

    assert references.get_head_commit() == current_commit