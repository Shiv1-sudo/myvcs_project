"""Garbage collection service."""

from datetime import UTC, datetime, timedelta

from myvcs.common.application_config import ApplicationConfig
from myvcs.common.application_logging import get_logger
from myvcs.storage.reachability import ReachabilityAnalyzer

LOGGER = get_logger(__name__)


class GarbageCollectionService:
    """Remove unreachable objects."""

    def __init__(
        self,
        repository,
        configuration: ApplicationConfig,
    ):
        self.repository = repository
        self.configuration = configuration

        self.reachability = ReachabilityAnalyzer(
            repository,
            configuration,
        )

    def collect(self) -> int:
        """Remove old unreachable objects."""

        reachable = self.reachability.find_reachable_objects()

        grace_days = int(
            self.configuration.require(
                "gc",
                "grace_period_days",
            )
        )

        cutoff = (datetime.now(UTC) - timedelta(days=grace_days)).timestamp()

        removed = 0

        for directory in self.repository.objects_directory.iterdir():
            if not directory.is_dir():
                continue

            for object_file in directory.iterdir():
                object_id = directory.name + object_file.name

                if object_id in reachable:
                    continue

                if object_file.stat().st_mtime > cutoff:
                    continue

                object_file.unlink()

                removed += 1

        LOGGER.info(
            "Garbage collection completed. Removed=%d",
            removed,
        )

        return removed
