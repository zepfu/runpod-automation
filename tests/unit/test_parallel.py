"""Tests for parallel batch execution helper."""

from __future__ import annotations

import pytest
from rpctl.services.parallel import (
    BatchResult,
    StopOnError,
    parallel_map,
)


def test_parallel_map_success():
    """All items succeed."""
    result = parallel_map(lambda x: x * 2, [1, 2, 3, 4, 5])
    assert result.all_ok
    assert result.total == 5
    assert sorted(result.succeeded) == [2, 4, 6, 8, 10]
    assert result.failed == []


def test_parallel_map_mixed_failures():
    """Some items fail, others succeed."""

    def maybe_fail(x):
        if x % 2 == 0:
            raise ValueError(f"Even number: {x}")
        return x

    result = parallel_map(maybe_fail, [1, 2, 3, 4, 5])
    assert not result.all_ok
    assert sorted(result.succeeded) == [1, 3, 5]
    assert len(result.failed) == 2
    # Failed items are the even numbers
    failed_items = sorted([item for item, _exc in result.failed])
    assert failed_items == [2, 4]


def test_parallel_map_stop_on_error():
    """stop_on_error=True raises on first failure."""
    call_count = 0

    def counting_fail(x):
        nonlocal call_count
        call_count += 1
        if x == 2:
            raise ValueError("fail")
        return x

    with pytest.raises(StopOnError):
        parallel_map(counting_fail, [1, 2, 3, 4, 5], stop_on_error=True)


def test_parallel_map_empty_list():
    """Empty list returns empty result."""
    result = parallel_map(lambda x: x, [])
    assert result.all_ok
    assert result.total == 0
    assert result.succeeded == []
    assert result.failed == []


def test_parallel_map_single_item():
    """Single item works correctly."""
    result = parallel_map(lambda x: x + 1, [10])
    assert result.all_ok
    assert result.succeeded == [11]


def test_parallel_map_max_workers_capped():
    """Workers are capped at MAX_WORKERS_CAP."""
    results = []

    def track(x):
        results.append(x)
        return x

    # Request more workers than cap
    result = parallel_map(track, list(range(50)), max_workers=100)
    assert result.all_ok
    assert result.total == 50


def test_parallel_map_max_workers_minimum():
    """Workers minimum is 1 even if 0 requested."""
    result = parallel_map(lambda x: x, [1, 2, 3], max_workers=0)
    assert result.all_ok
    assert result.total == 3


def test_batch_result_properties():
    """BatchResult properties work correctly."""
    br = BatchResult()
    assert br.total == 0
    assert br.all_ok

    br.succeeded.append("a")
    assert br.total == 1
    assert br.all_ok

    br.failed.append(("b", ValueError("err")))
    assert br.total == 2
    assert not br.all_ok


def test_parallel_map_preserves_exception_types():
    """Failed items preserve the original exception type."""

    def raise_type_error(x):
        raise TypeError(f"bad type: {x}")

    result = parallel_map(raise_type_error, [1])
    assert len(result.failed) == 1
    _item, exc = result.failed[0]
    assert isinstance(exc, TypeError)
