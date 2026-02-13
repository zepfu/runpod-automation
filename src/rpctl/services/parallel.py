"""Parallel execution helper using ThreadPoolExecutor."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")
R = TypeVar("R")

MAX_WORKERS_CAP = 20


@dataclass
class BatchResult:
    """Result of a parallel batch operation."""

    succeeded: list[Any] = field(default_factory=list)
    failed: list[tuple[Any, Exception]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def all_ok(self) -> bool:
        return len(self.failed) == 0


class StopOnError(Exception):
    """Raised when stop_on_error is True and a task fails."""


def parallel_map(
    func: Callable[[Any], Any],
    items: list[Any],
    *,
    max_workers: int = 5,
    stop_on_error: bool = False,
) -> BatchResult:
    """Execute func on each item in parallel using threads.

    Args:
        func: Callable that takes a single item and returns a result.
        items: List of items to process.
        max_workers: Maximum concurrent threads (capped at MAX_WORKERS_CAP).
        stop_on_error: If True, raise StopOnErrorException on first failure.

    Returns:
        BatchResult with succeeded and failed lists.
    """
    if not items:
        return BatchResult()

    workers = min(max(1, max_workers), MAX_WORKERS_CAP, len(items))
    result = BatchResult()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {executor.submit(func, item): item for item in items}

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                value = future.result()
                result.succeeded.append(value)
            except Exception as exc:
                result.failed.append((item, exc))
                if stop_on_error:
                    # Cancel remaining futures
                    for f in future_to_item:
                        f.cancel()
                    raise StopOnError(f"Stopped on error processing {item}: {exc}") from exc

    return result
