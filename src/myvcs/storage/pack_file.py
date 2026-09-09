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

        self.index_extension = configuration.require(
            "pack",
            "index_extension",
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

        pack_file = self.pack_directory / f"{pack_name}{self.extension}"
        index_file = self.pack_directory / f"{pack_name}{self.index_extension}"

        index: dict[str, int] = {}

        with pack_file.open("wb") as file:
            for object_id, data in objects.items():
                offset = file.tell()

                record = {
                    "object_id": object_id,
                    "size": len(data),
                    "data": data.hex(),
                }

                encoded = json.dumps(record).encode("utf-8") + b"\n"

                file.write(encoded)

                index[object_id] = offset

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

    def lookup(
        self,
        object_id: str,
    ) -> tuple[Path, int] | None:
        """Find an object in the pack indexes."""

        if not self.pack_directory.exists():
            return None

        for index_file in self.pack_directory.glob(
            f"*{self.index_extension}",
        ):
            try:
                index = json.loads(
                    index_file.read_text(
                        encoding="utf-8",
                    )
                )

                if object_id not in index:
                    continue

                pack_file = index_file.with_suffix(
                    self.extension,
                )

                if not pack_file.exists():
                    LOGGER.warning(
                        "Pack index exists without pack file: %s",
                        index_file,
                    )
                    continue

                return pack_file, int(index[object_id])

            except (OSError, ValueError, json.JSONDecodeError):
                LOGGER.exception(
                    "Unable to read pack index: %s",
                    index_file,
                )

        return None

    def read(
        self,
        object_id: str,
    ) -> bytes | None:
        """Read a packed object."""

        result = self.lookup(object_id)

        if result is None:
            return None

        pack_file, offset = result

        try:
            with pack_file.open("rb") as file:
                file.seek(offset)
                line = file.readline()

            if not line:
                return None

            record = json.loads(
                line.decode("utf-8"),
            )

            if record.get("object_id") != object_id:
                LOGGER.error(
                    "Pack index mismatch for object: %s",
                    object_id,
                )
                return None

            data = bytes.fromhex(record["data"])

            if len(data) != int(record["size"]):
                LOGGER.error(
                    "Packed object size mismatch: %s",
                    object_id,
                )
                return None

            return data

        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            LOGGER.exception(
                "Unable to read packed object: %s",
                object_id,
            )

            return None