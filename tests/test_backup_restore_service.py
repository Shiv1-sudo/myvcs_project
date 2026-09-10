
"""Tests for repository backup and restore services."""

from pathlib import Path

import pytest

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_exceptions import RepositoryError
from myvcs.repository.repository_manager import RepositoryManager
from myvcs.services.backup_service import BackupService
from myvcs.services.restore_service import RestoreService


@pytest.fixture
def configuration() -> ApplicationConfig:
    """Return test application configuration."""

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
            "references": {
                "default_branch": "main",
                "head_prefix": "ref: ",
                "heads_reference_prefix": "refs/heads/",
                "tags_reference_prefix": "refs/tags/",
                "remotes_reference_prefix": "refs/remotes/",
            },
        }
    )


@pytest.fixture
def repository(
    tmp_path: Path,
    configuration: ApplicationConfig,
) -> RepositoryManager:
    """Create and initialize a test repository."""

    repository = RepositoryManager(
        working_directory=tmp_path,
        configuration=configuration,
    )

    repository.initialize()

    return repository


def test_backup_creates_backup_directory(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Backup should create a copy of the repository metadata."""

    backup_path = tmp_path / "repository-backup"

    service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    result = service.backup(str(backup_path))

    assert result == backup_path.resolve()
    assert backup_path.is_dir()

    assert (backup_path / "HEAD").is_file()
    assert (backup_path / "objects").is_dir()
    assert (backup_path / "refs").is_dir()


def test_backup_preserves_repository_files(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Backup should preserve repository metadata files."""

    repository.head_file.write_text(
        "ref: refs/heads/main\n",
        encoding="utf-8",
    )

    repository.index_file.write_text(
        "test-index-data\n",
        encoding="utf-8",
    )

    backup_path = tmp_path / "repository-backup"

    service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    service.backup(str(backup_path))

    assert (
        backup_path / "HEAD"
    ).read_text(encoding="utf-8") == "ref: refs/heads/main\n"

    assert (
        backup_path / "index"
    ).read_text(encoding="utf-8") == "test-index-data\n"


def test_backup_existing_destination_raises_error(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Backup should reject an existing destination."""

    backup_path = tmp_path / "repository-backup"
    backup_path.mkdir()

    service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    with pytest.raises(RepositoryError, match="already exists"):
        service.backup(str(backup_path))


def test_backup_without_repository_raises_error(
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Backup should fail when no repository exists."""

    repository = RepositoryManager(
        working_directory=tmp_path,
        configuration=configuration,
    )

    service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    backup_path = tmp_path / "repository-backup"

    with pytest.raises(RepositoryError, match="No MyVCS repository found"):
        service.backup(str(backup_path))


def test_backup_destination_cannot_be_repository_metadata(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Backup destination cannot be the active metadata directory."""

    service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    with pytest.raises(RepositoryError, match="cannot be the repository"):
        service.backup(str(repository.metadata_directory))


def test_restore_restores_repository_metadata(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Restore should restore metadata from a backup."""

    repository.head_file.write_text(
        "ref: refs/heads/main\n",
        encoding="utf-8",
    )

    repository.index_file.write_text(
        "original-index\n",
        encoding="utf-8",
    )

    backup_path = tmp_path / "repository-backup"

    backup_service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    backup_service.backup(str(backup_path))

    repository.head_file.write_text(
        "corrupted-head\n",
        encoding="utf-8",
    )

    repository.index_file.write_text(
        "corrupted-index\n",
        encoding="utf-8",
    )

    restore_service = RestoreService(
        repository=repository,
        configuration=configuration,
    )

    restore_service.restore(str(backup_path))

    assert (
        repository.head_file.read_text(encoding="utf-8")
        == "ref: refs/heads/main\n"
    )

    assert (
        repository.index_file.read_text(encoding="utf-8")
        == "original-index\n"
    )


def test_restore_preserves_repository_structure(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Restore should preserve repository directories."""

    backup_path = tmp_path / "repository-backup"

    backup_service = BackupService(
        repository=repository,
        configuration=configuration,
    )

    backup_service.backup(str(backup_path))

    restore_service = RestoreService(
        repository=repository,
        configuration=configuration,
    )

    restore_service.restore(str(backup_path))

    assert repository.metadata_directory.is_dir()
    assert repository.objects_directory.is_dir()
    assert repository.references_directory.is_dir()
    assert repository.heads_directory.is_dir()
    assert repository.tags_directory.is_dir()
    assert repository.head_file.is_file()


def test_restore_missing_backup_raises_error(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
    tmp_path: Path,
) -> None:
    """Restore should fail when the backup directory does not exist."""

    missing_backup = tmp_path / "missing-backup"

    service = RestoreService(
        repository=repository,
        configuration=configuration,
    )

    with pytest.raises(
        RepositoryError,
        match="Backup directory does not exist",
    ):
        service.restore(str(missing_backup))


def test_restore_from_repository_metadata_raises_error(
    repository: RepositoryManager,
    configuration: ApplicationConfig,
) -> None:
    """Restore source cannot be the active metadata directory."""

    service = RestoreService(
        repository=repository,
        configuration=configuration,
    )

    with pytest.raises(
        RepositoryError,
        match="cannot be the repository metadata directory",
    ):
        service.restore(str(repository.metadata_directory))
 
