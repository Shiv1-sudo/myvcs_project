"""Staging index tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.staging.staging_index import StagingIndex


def create_configuration() -> ApplicationConfig:
    """Create test configuration."""

    return ApplicationConfig(
        {
            "index": {
                "version": 1,
            },
        }
    )


def test_staging_index(
    tmp_path: Path,
):
    """Index should save and load staged files."""

    configuration = create_configuration()

    index = StagingIndex(
        index_file=tmp_path / "index",
        configuration=configuration,
    )

    index.add(
        "hello.txt",
        "abc123",
    )

    entries = index.load()

    assert entries == {
        "hello.txt": "abc123"
    }