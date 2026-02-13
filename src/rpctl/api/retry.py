"""Retry logic for transient API failures."""

from __future__ import annotations

import logging
import random
import time
from typing import Any, TypeVar

from rpctl.config.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BASE_DELAY,
    DEFAULT_RETRY_MAX_DELAY,
)
from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_transient(
    func: Any,
    *args: Any,
    max_attempts: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    max_delay: float = DEFAULT_RETRY_MAX_DELAY,
    **kwargs: Any,
) -> Any:
    """Call *func* with exponential backoff + jitter on transient errors.

    Retries on:
    - ``ApiError`` where ``is_transient`` is True
    - ``ConnectionError``, ``TimeoutError``, ``OSError`` (network-level)

    Does NOT retry on:
    - ``AuthenticationError``, ``ResourceNotFoundError``
    - ``ApiError`` with non-transient status codes (400, 401, 403, 404, 422)
    """
    last_exception: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)

        except (AuthenticationError, ResourceNotFoundError):
            raise

        except ApiError as e:
            last_exception = e
            if not e.is_transient or attempt == max_attempts:
                raise
            delay = _calculate_delay(
                attempt,
                base_delay,
                max_delay,
                retry_after=getattr(e, "retry_after", None),
            )
            logger.warning(
                "Transient error (attempt %d/%d): %s. Retrying in %.1fs",
                attempt,
                max_attempts,
                e,
                delay,
            )
            time.sleep(delay)

        except (ConnectionError, TimeoutError, OSError) as e:
            last_exception = e
            if attempt == max_attempts:
                raise ApiError(
                    f"Connection failed after {max_attempts} attempts: {e}",
                ) from e
            delay = _calculate_delay(attempt, base_delay, max_delay)
            logger.warning(
                "Connection error (attempt %d/%d): %s. Retrying in %.1fs",
                attempt,
                max_attempts,
                e,
                delay,
            )
            time.sleep(delay)

    raise last_exception  # type: ignore[misc]  # unreachable but satisfies type checker


def _calculate_delay(
    attempt: int,
    base: float,
    max_delay: float,
    retry_after: float | None = None,
) -> float:
    """Compute delay with exponential backoff, jitter, or Retry-After."""
    if retry_after is not None and retry_after > 0:
        return float(min(retry_after, max_delay))
    delay = base * (2 ** (attempt - 1))
    jitter = random.uniform(0, delay * 0.5)  # noqa: S311
    return float(min(delay + jitter, max_delay))
