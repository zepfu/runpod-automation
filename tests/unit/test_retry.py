"""Unit tests for retry logic."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rpctl.api.retry import _calculate_delay, retry_on_transient
from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError


@patch("rpctl.api.retry.time.sleep")
def test_no_retry_on_success(mock_sleep):
    """Successful function should be called once, no retry."""
    result = retry_on_transient(lambda: "ok")
    assert result == "ok"
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_retry_on_transient_error(mock_sleep):
    """Transient ApiError should be retried up to max_attempts."""
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ApiError("server error", status_code=500)
        return "recovered"

    result = retry_on_transient(flaky, max_attempts=3)
    assert result == "recovered"
    assert call_count == 3
    assert mock_sleep.call_count == 2


@patch("rpctl.api.retry.time.sleep")
def test_no_retry_on_permanent_error(mock_sleep):
    """Non-transient ApiError should raise immediately."""

    def bad_request():
        raise ApiError("bad request", status_code=400)

    with pytest.raises(ApiError, match="bad request"):
        retry_on_transient(bad_request)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_no_retry_on_auth_error(mock_sleep):
    """AuthenticationError should never be retried."""

    def auth_fail():
        raise AuthenticationError("Invalid API key.")

    with pytest.raises(AuthenticationError):
        retry_on_transient(auth_fail)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_no_retry_on_not_found(mock_sleep):
    """ResourceNotFoundError should never be retried."""

    def not_found():
        raise ResourceNotFoundError("Pod not found.")

    with pytest.raises(ResourceNotFoundError):
        retry_on_transient(not_found)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_retry_on_connection_error(mock_sleep):
    """ConnectionError should be retried."""
    call_count = 0

    def flaky_network():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("refused")
        return "connected"

    result = retry_on_transient(flaky_network, max_attempts=3)
    assert result == "connected"
    assert call_count == 2
    assert mock_sleep.call_count == 1


@patch("rpctl.api.retry.time.sleep")
def test_retry_on_timeout_error(mock_sleep):
    """TimeoutError should be retried."""
    call_count = 0

    def slow():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise TimeoutError("timed out")
        return "done"

    result = retry_on_transient(slow, max_attempts=3)
    assert result == "done"
    assert call_count == 2


@patch("rpctl.api.retry.time.sleep")
def test_retry_on_os_error(mock_sleep):
    """OSError should be retried."""
    call_count = 0

    def network_unreachable():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise OSError("Network unreachable")
        return "ok"

    result = retry_on_transient(network_unreachable, max_attempts=3)
    assert result == "ok"
    assert call_count == 2


@patch("rpctl.api.retry.time.sleep")
def test_max_attempts_exhausted_transient(mock_sleep):
    """Should raise after max_attempts on persistent transient errors."""

    def always_fail():
        raise ApiError("server down", status_code=503)

    with pytest.raises(ApiError, match="server down"):
        retry_on_transient(always_fail, max_attempts=3)
    assert mock_sleep.call_count == 2  # sleeps between attempts 1-2 and 2-3


@patch("rpctl.api.retry.time.sleep")
def test_max_attempts_exhausted_connection(mock_sleep):
    """ConnectionError should wrap in ApiError after max attempts."""

    def always_fail():
        raise ConnectionError("refused")

    with pytest.raises(ApiError, match="Connection failed after 3 attempts"):
        retry_on_transient(always_fail, max_attempts=3)


@patch("rpctl.api.retry.time.sleep")
def test_respects_retry_after(mock_sleep):
    """Should use Retry-After value when present on error."""
    call_count = 0

    def rate_limited():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            err = ApiError("rate limited", status_code=429)
            err.retry_after = 5.0  # type: ignore[attr-defined]
            raise err
        return "ok"

    result = retry_on_transient(rate_limited, max_attempts=3)
    assert result == "ok"
    # Should have slept for 5.0 seconds (the Retry-After value)
    mock_sleep.assert_called_once()
    assert mock_sleep.call_args[0][0] == 5.0


@patch("rpctl.api.retry.time.sleep")
def test_retry_after_capped_by_max_delay(mock_sleep):
    """Retry-After value should be capped by max_delay."""
    call_count = 0

    def rate_limited():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            err = ApiError("rate limited", status_code=429)
            err.retry_after = 120.0  # type: ignore[attr-defined]
            raise err
        return "ok"

    result = retry_on_transient(rate_limited, max_attempts=3, max_delay=10.0)
    assert result == "ok"
    assert mock_sleep.call_args[0][0] == 10.0


def test_calculate_delay_exponential():
    """Delay should increase exponentially."""
    with patch("rpctl.api.retry.random.uniform", return_value=0):
        d1 = _calculate_delay(1, base=1.0, max_delay=30.0)
        d2 = _calculate_delay(2, base=1.0, max_delay=30.0)
        d3 = _calculate_delay(3, base=1.0, max_delay=30.0)
    assert d1 == 1.0
    assert d2 == 2.0
    assert d3 == 4.0


def test_calculate_delay_capped():
    """Delay should not exceed max_delay."""
    with patch("rpctl.api.retry.random.uniform", return_value=0):
        d = _calculate_delay(10, base=1.0, max_delay=5.0)
    assert d == 5.0


def test_calculate_delay_has_jitter():
    """Delay should include jitter (randomness)."""
    delays = set()
    for _ in range(20):
        d = _calculate_delay(1, base=1.0, max_delay=30.0)
        delays.add(round(d, 4))
    # With jitter, we should see multiple distinct values
    assert len(delays) > 1


def test_calculate_delay_with_retry_after():
    """Should use Retry-After value directly."""
    d = _calculate_delay(1, base=1.0, max_delay=30.0, retry_after=7.5)
    assert d == 7.5


@patch("rpctl.api.retry.time.sleep")
def test_retry_429_then_500_then_success(mock_sleep):
    """Mixed transient errors should all be retried."""
    call_count = 0

    def mixed_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ApiError("rate limited", status_code=429)
        if call_count == 2:
            raise ApiError("internal error", status_code=500)
        return "ok"

    result = retry_on_transient(mixed_errors, max_attempts=3)
    assert result == "ok"
    assert call_count == 3


@patch("rpctl.api.retry.time.sleep")
def test_no_retry_on_none_status_code(mock_sleep):
    """ApiError with no status code is not transient."""

    def graphql_error():
        raise ApiError("GraphQL error: invalid query")

    with pytest.raises(ApiError, match="invalid query"):
        retry_on_transient(graphql_error)
    mock_sleep.assert_not_called()
