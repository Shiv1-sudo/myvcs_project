"""Application configuration management."""

from pathlib import Path
from typing import Any

import yaml

from myvcs.common.application_constants import (
    APPLICATION_CONFIG_FILE_NAME,
    CONFIGURATION_DIRECTORY_NAME,
)
from myvcs.common.application_exceptions import ConfigurationError


class ApplicationConfig:
    """Provides access to application configuration."""

    def __init__(self, values: dict[str, Any]):
        self._values = values

    def get(
        self,
        *keys: str,
        default: Any = None,
    ) -> Any:
        """Retrieve a nested configuration value."""

        current_value: Any = self._values

        try:
            for key in keys:
                current_value = current_value[key]

            return current_value

        except (KeyError, TypeError) as exc:
            if default is not None:
                return default

            key_path = ".".join(keys)

            raise ConfigurationError(
                f"Configuration value not found: {key_path}"
            ) from exc

    def require(
        self,
        *keys: str,
    ) -> Any:
        """Retrieve a mandatory configuration value."""

        return self.get(*keys)


def locate_configuration_file() -> Path:
    """Locate application configuration."""

    package_directory = Path(__file__).resolve().parents[2]

    project_root = package_directory.parent

    return (
        project_root
        / CONFIGURATION_DIRECTORY_NAME
        / APPLICATION_CONFIG_FILE_NAME
    )


def load_configuration() -> ApplicationConfig:
    """Load configuration from YAML."""

    configuration_file = locate_configuration_file()

    try:
        with configuration_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            values = yaml.safe_load(file)

        if not isinstance(values, dict):
            raise ConfigurationError(
                "Application configuration must be a YAML mapping."
            )

        return ApplicationConfig(values)

    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Configuration file not found: {configuration_file}"
        ) from exc

    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML configuration: {configuration_file}"
        ) from exc