"""Application-level constants."""

from pathlib import Path

PACKAGE_NAME = "myvcs"
SOURCE_DIRECTORY_NAME = "src"
CONFIGURATION_DIRECTORY_NAME = "configuration"

APPLICATION_CONFIG_FILE_NAME = "application.yaml"

UTF8_ENCODING = "utf-8"

EMPTY_STRING = ""
NEWLINE = "\n"

OBJECT_ID_LENGTH = 64
OBJECT_DIRECTORY_PREFIX_LENGTH = 2

DEFAULT_FILE_MODE = 0o644

PROJECT_ROOT_MARKERS = (
    "pyproject.toml",
    "README.md",
)


def find_project_root(start_directory: Path) -> Path:
    """Find the project root directory."""

    current_directory = start_directory.resolve()

    for directory in (
        current_directory,
        *current_directory.parents,
    ):
        if all((directory / marker).exists() for marker in PROJECT_ROOT_MARKERS):
            return directory

    return current_directory
