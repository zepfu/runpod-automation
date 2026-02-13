"""Shared polling utility for wait commands."""

from __future__ import annotations

import time
from collections.abc import Callable

from rich.console import Console

err_console = Console(stderr=True)


class PollTimeoutError(Exception):
    """Raised when polling exceeds the timeout."""


def poll_until(
    check_fn: Callable[[], tuple[bool, str]],
    *,
    timeout: float = 300,
    interval: float = 5,
    label: str = "resource",
) -> None:
    """Poll check_fn until it returns (True, status) or timeout.

    Args:
        check_fn: Returns (done, status_message). Called every interval seconds.
        timeout: Max seconds to wait.
        interval: Seconds between polls.
        label: Resource name for status messages.

    Raises:
        PollTimeoutError: If timeout is exceeded.
    """
    deadline = time.monotonic() + timeout
    last_status = ""

    while True:
        done, status = check_fn()

        if status != last_status:
            err_console.print(f"[dim]{label}: {status}[/dim]")
            last_status = status

        if done:
            return

        if time.monotonic() >= deadline:
            raise PollTimeoutError(
                f"Timed out after {timeout}s waiting for {label}. Last status: {status}"
            )

        remaining = deadline - time.monotonic()
        time.sleep(min(interval, max(0, remaining)))
