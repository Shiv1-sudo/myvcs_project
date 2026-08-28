"""Simple MyVCS pack file implementation."""

import json
from pathlib import Path

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger


LOGGER = get_logger(__name__)


class PackFile:
    """Create and read packed objects."""

    def __init__(
        self,
        pack_directory: Path,
        configuration: ApplicationConfig,
    ):
        self.pack_directory = pack_directory
        self.configuration = configuration

        self.extension = configuration.require(
            "pack",
            "extension",
        )

        self.index_extension = (
            configuration.require(
                "pack",
                "index_extension",
            )
        )

    def create(
        self,
        objects: dict[str, bytes],
        pack_name: str,
    ) -> Path:
        """Create pack file."""

        self.pack_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        pack_file = (
            self.pack_directory
            / f"{pack_name}{self.extension}"
        )

        index_file = (
            self.pack_directory
            / f"{pack_name}{self.index_extension}"
        )

        index: dict[str, int] = {}

        with pack_file.open(
            "wb"
        ) as file:
            for object_id, data in objects.items():
                offset = file.tell()

                record = {
                    "object_id": object_id,
                    "size": len(data),
                    "data": data.hex(),
                }

                encoded = (
                    json.dumps(record)
                    .encode("utf-8")
                    + b"\n"
                )

                file.write(encoded)

                index[
                    object_id
                ] = offset

        index_file.write_text(
            json.dumps(
                index,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        LOGGER.info(
            "Pack created: %s Objects=%d",
            pack_file,
            len(objects),
        )

        return pack_file