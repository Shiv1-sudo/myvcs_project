"""Object store tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.objects.blob_object import BlobObject
from myvcs.repository.object_store import ObjectStore


def create_configuration() -> ApplicationConfig:
    """Create test configuration."""

    return ApplicationConfig(
        {
            "objects": {
                "hash_algorithm": "sha256",
                "blob_type": "blob",
            },
        }
    )


def test_blob_is_stored(
    tmp_path: Path,
):
    """Blob should be stored and readable."""

    configuration = create_configuration()

    object_store = ObjectStore(
        objects_directory=tmp_path,
        configuration=configuration,
    )

    blob = BlobObject(
        data=b"Hello MyVCS",
        configuration=configuration,
    )

    object_id = object_store.write(
        blob
    )

    assert object_store.exists(
        object_id
    )

    stored_data = object_store.read(
        object_id
    )

    assert stored_data == blob.serialize()