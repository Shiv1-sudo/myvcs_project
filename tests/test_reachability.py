"""Reachability analyzer tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.blob_object import BlobObject
from myvcs.objects.commit_object import CommitObject
from myvcs.objects.tree_object import TreeEntry, TreeObject
from myvcs.references.reference_manager import ReferenceManager
from myvcs.repository.object_store import ObjectStore
from myvcs.repository.repository_manager import RepositoryManager
from myvcs.storage.reachability import ReachabilityAnalyzer


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
                "default_branch": "main",
            },
        }
    )


def create_repository(
    tmp_path: Path,
):
    """Create a test repository."""

    configuration = create_configuration()

    repository = RepositoryManager(
        tmp_path,
        configuration,
    )

    repository.initialize()

    return repository, configuration


def create_commit_graph(
    repository,
    configuration: ApplicationConfig,
):
    """Create a commit, tree, and blob graph."""

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    blob = BlobObject(
        data=b"hello MyVCS",
        configuration=configuration,
    )

    blob_id = object_store.write(blob)

    tree = TreeObject(
        entries=[
            TreeEntry(
                name="hello.txt",
                object_id=blob_id,
                object_type="blob",
            ),
        ],
        configuration=configuration,
    )

    tree_id = object_store.write(tree)

    commit = CommitObject(
        tree_id=tree_id,
        parent_id=None,
        message="Initial commit",
        author="Developer",
        configuration=configuration,
    )

    commit_id = object_store.write(commit)

    return commit_id, tree_id, blob_id


def test_reachable_commit_tree_and_blob(
    tmp_path: Path,
):
    """Reachability should include the complete commit graph."""

    repository, configuration = create_repository(tmp_path)

    commit_id, tree_id, blob_id = create_commit_graph(
        repository,
        configuration,
    )

    references = ReferenceManager(
        repository,
        configuration,
    )

    references.update_head(commit_id)

    analyzer = ReachabilityAnalyzer(
        repository,
        configuration,
    )

    reachable = analyzer.find_reachable_objects()

    assert commit_id in reachable
    assert tree_id in reachable
    assert blob_id in reachable


def test_unreachable_object_is_excluded(
    tmp_path: Path,
):
    """Objects not referenced by branches or tags should be excluded."""

    repository, configuration = create_repository(tmp_path)

    commit_id, tree_id, blob_id = create_commit_graph(
        repository,
        configuration,
    )

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    unreachable_blob = BlobObject(
        data=b"unreachable object",
        configuration=configuration,
    )

    unreachable_id = object_store.write(unreachable_blob)

    references = ReferenceManager(
        repository,
        configuration,
    )

    references.update_head(commit_id)

    analyzer = ReachabilityAnalyzer(
        repository,
        configuration,
    )

    reachable = analyzer.find_reachable_objects()

    assert commit_id in reachable
    assert tree_id in reachable
    assert blob_id in reachable
    assert unreachable_id not in reachable


def test_tag_makes_commit_graph_reachable(
    tmp_path: Path,
):
    """A tag should make its commit graph reachable."""

    repository, configuration = create_repository(tmp_path)

    commit_id, tree_id, blob_id = create_commit_graph(
        repository,
        configuration,
    )

    references = ReferenceManager(
        repository,
        configuration,
    )

    references.create_tag(
        "release",
        commit_id,
    )

    analyzer = ReachabilityAnalyzer(
        repository,
        configuration,
    )

    reachable = analyzer.find_reachable_objects()

    assert commit_id in reachable
    assert tree_id in reachable
    assert blob_id in reachable


def test_parent_commit_is_reachable(
    tmp_path: Path,
):
    """Reachability should walk through parent commits."""

    repository, configuration = create_repository(tmp_path)

    object_store = ObjectStore(
        repository.objects_directory,
        configuration,
    )

    blob = BlobObject(
        data=b"hello",
        configuration=configuration,
    )

    blob_id = object_store.write(blob)

    tree = TreeObject(
        entries=[
            TreeEntry(
                name="hello.txt",
                object_id=blob_id,
                object_type="blob",
            ),
        ],
        configuration=configuration,
    )

    tree_id = object_store.write(tree)

    first_commit = CommitObject(
        tree_id=tree_id,
        parent_id=None,
        message="Initial commit",
        author="Developer",
        configuration=configuration,
    )

    first_commit_id = object_store.write(first_commit)

    second_commit = CommitObject(
        tree_id=tree_id,
        parent_id=first_commit_id,
        message="Second commit",
        author="Developer",
        configuration=configuration,
    )

    second_commit_id = object_store.write(second_commit)

    references = ReferenceManager(
        repository,
        configuration,
    )

    references.update_head(second_commit_id)

    analyzer = ReachabilityAnalyzer(
        repository,
        configuration,
    )

    reachable = analyzer.find_reachable_objects()

    assert second_commit_id in reachable
    assert first_commit_id in reachable
    assert tree_id in reachable
    assert blob_id in reachable