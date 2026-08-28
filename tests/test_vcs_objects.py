"""VCS object tests."""

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.blob_object import BlobObject
from myvcs.objects.commit_object import CommitObject
from myvcs.objects.tree_object import TreeObject


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
        }
    )


def test_blob_object():
    """Blob should have the configured type."""

    configuration = create_configuration()

    blob = BlobObject(
        data=b"hello",
        configuration=configuration,
    )

    assert blob.object_type == "blob"


def test_tree_object():
    """Tree should contain staged entries."""

    configuration = create_configuration()

    tree = TreeObject(
        entries={"hello.txt": "abc123"},
        configuration=configuration,
    )

    serialized = tree.serialize()

    assert b"tree " in serialized
    assert b"hello.txt abc123" in serialized


def test_commit_object():
    """Commit should contain tree and parent."""

    configuration = create_configuration()

    commit = CommitObject(
        tree_id="tree123",
        parent_id="parent123",
        message="Initial commit",
        author="Developer",
        configuration=configuration,
    )

    serialized = commit.serialize()

    assert b"commit " in serialized
    assert b"tree tree123" in serialized
    assert b"parent parent123" in serialized
    assert b"Initial commit" in serialized
