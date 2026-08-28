"""Repository manager tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.repository.repository_manager import (
    RepositoryManager,
)


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
                "head_prefix": "ref: ",
                "heads_reference_prefix": "refs/heads/",
                "default_branch": "main",
            },
        }
    )


def test_repository_initialization(
    tmp_path: Path,
):
    """Repository should initialize correctly."""

    configuration = create_configuration()

    repository = RepositoryManager(
        working_directory=tmp_path,
        configuration=configuration,
    )

    repository.initialize()

    assert repository.metadata_directory.exists()
    assert repository.objects_directory.exists()
    assert repository.references_directory.exists()
    assert repository.heads_directory.exists()
    assert repository.tags_directory.exists()
    assert repository.head_file.exists()

    assert repository.head_file.read_text(encoding="utf-8") == "ref: refs/heads/main\n"
