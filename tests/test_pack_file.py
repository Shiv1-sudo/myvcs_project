"""Pack file tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.storage.pack_file import PackFile


def create_configuration() -> ApplicationConfig:
    """Create test configuration."""

    return ApplicationConfig(
        {
            "pack": {
                "extension": ".pack",
                "index_extension": ".idx",
            },
        }
    )


def test_pack_file_create_and_read(
    tmp_path: Path,
):
    """Packed objects should be readable."""

    configuration = create_configuration()

    pack_file = PackFile(
        pack_directory=tmp_path,
        configuration=configuration,
    )

    objects = {
        "abc123": b"hello MyVCS",
        "def456": b"second object",
    }

    pack_file.create(
        objects,
        "pack-test",
    )

    assert pack_file.read("abc123") == b"hello MyVCS"
    assert pack_file.read("def456") == b"second object"


def test_pack_file_lookup(
    tmp_path: Path,
):
    """Pack index should locate an object."""

    configuration = create_configuration()

    pack_file = PackFile(
        pack_directory=tmp_path,
        configuration=configuration,
    )

    pack_file.create(
        {
            "abc123": b"hello",
        },
        "pack-test",
    )

    result = pack_file.lookup("abc123")

    assert result is not None

    pack_path, offset = result

    assert pack_path.name == "pack-test.pack"
    assert offset >= 0


def test_pack_file_missing_object(
    tmp_path: Path,
):
    """Missing packed objects should return None."""

    configuration = create_configuration()

    pack_file = PackFile(
        pack_directory=tmp_path,
        configuration=configuration,
    )

    pack_file.create(
        {
            "abc123": b"hello",
        },
        "pack-test",
    )

    assert pack_file.read("missing") is None
    assert pack_file.lookup("missing") is None