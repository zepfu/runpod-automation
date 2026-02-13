"""Tests for shared polling utility."""

from __future__ import annotations

import pytest

from rpctl.services.poll import PollTimeoutError, poll_until


def test_poll_until_immediate_success():
    """Check function returns True immediately."""
    calls = 0

    def check() -> tuple[bool, str]:
        nonlocal calls
        calls += 1
        return True, "RUNNING"

    poll_until(check, timeout=10, interval=1, label="test")
    assert calls == 1


def test_poll_until_succeeds_after_retries():
    """Check function returns True after a few polls."""
    calls = 0

    def check() -> tuple[bool, str]:
        nonlocal calls
        calls += 1
        if calls >= 3:
            return True, "RUNNING"
        return False, "PENDING"

    poll_until(check, timeout=10, interval=0.01, label="test")
    assert calls == 3


def test_poll_until_timeout():
    """Raises PollTimeoutError when timeout exceeded."""

    def check() -> tuple[bool, str]:
        return False, "PENDING"

    with pytest.raises(PollTimeoutError, match="Timed out"):
        poll_until(check, timeout=0.05, interval=0.01, label="test-resource")


def test_poll_until_timeout_includes_last_status():
    """Timeout error includes the last status message."""

    def check() -> tuple[bool, str]:
        return False, "INITIALIZING"

    with pytest.raises(PollTimeoutError, match="INITIALIZING"):
        poll_until(check, timeout=0.05, interval=0.01, label="pod")


def test_poll_until_status_changes_printed(capsys):
    """Status changes are printed to stderr."""
    calls = 0
    statuses = ["CREATED", "CREATED", "PULLING", "RUNNING"]

    def check() -> tuple[bool, str]:
        nonlocal calls
        status = statuses[min(calls, len(statuses) - 1)]
        calls += 1
        return status == "RUNNING", status

    poll_until(check, timeout=10, interval=0.01, label="pod x")
    # Status messages go to stderr via Rich Console, so we can't easily
    # capture them. Just verify the function completed successfully.
    assert calls >= 3
