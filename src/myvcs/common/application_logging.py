
"""Application logging configuration."""

import logging
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_constants import find_project_root


def configure_logging(
    configuration: ApplicationConfig,
) -> None:
    """Configure application logging."""

    log_level = configuration.require(
        "logging",
        "level",
    )

    configured_log_directory = Path(
        configuration.require(
            "logging",
            "directory",
        )
    )

    log_filename = configuration.require(
        "logging",
        "filename",
    )

    log_format = configuration.require(
        "logging",
        "format",
    )

    if configured_log_directory.is_absolute():
        log_directory = configured_log_directory
    else:
        project_root = find_project_root(
            Path(__file__).resolve().parent
        )

        # When running from an installed Docker image, the project root
        # may not contain pyproject.toml. In that case, use /app.
        if not (
            (project_root / "pyproject.toml").exists()
            and (project_root / "README.md").exists()
        ):
            project_root = Path("/app")

        log_directory = project_root / configured_log_directory

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / log_filename

    logging.basicConfig(
        level=getattr(
            logging,
            str(log_level).upper(),
        ),
        format=log_format,
        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


def get_logger(
    name: str,
) -> logging.Logger:
    """Return a logger for a component."""

    return logging.getLogger(name)

