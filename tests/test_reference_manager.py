"""Reference manager tests."""

from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.references.reference_manager import (
    ReferenceManager,
)
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


def test_reference_manager(
    tmp_path: Path,
):
    """Reference manager should read and update HEAD."""

    configuration = create_configuration()

    repository = RepositoryManager(
        working_directory=tmp_path,
        configuration=configuration,
    )

    repository.initialize()

    references = ReferenceManager(
        repository=repository,
        configuration=configuration,
    )

    assert references.current_branch() == "main"

    assert references.get_head_commit() is None

    references.update_head("abc123")

    assert references.get_head_commit() == "abc123"
