"""GraphQL client for RunPod capacity and availability queries."""

from __future__ import annotations

import contextlib
import logging

import httpx

from rpctl.config.constants import DEFAULT_API_TIMEOUT, GRAPHQL_URL
from rpctl.errors import ApiError, AuthenticationError

logger = logging.getLogger(__name__)


class GraphQLClient:
    """Thin GraphQL client using httpx with automatic retry on transient errors."""

    def __init__(
        self,
        api_key: str,
        base_url: str = GRAPHQL_URL,
        timeout: float = DEFAULT_API_TIMEOUT,
    ):
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def execute(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query with automatic retry on transient errors."""
        from rpctl.api.retry import retry_on_transient

        return retry_on_transient(self._execute_once, query, variables)

    def _execute_once(self, query: str, variables: dict | None = None) -> dict:
        """Execute a single GraphQL request (no retry)."""
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug("GraphQL request: %s", query[:80])

        try:
            response = self._client.post("", json=payload)
        except httpx.ConnectError as e:
            raise ApiError(f"Cannot connect to RunPod API: {e}", status_code=503) from e
        except httpx.TimeoutException as e:
            raise ApiError(f"Request timed out: {e}", status_code=408) from e

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key.")

        if response.status_code == 429:
            err = ApiError("Rate limited by RunPod API", status_code=429)
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                with contextlib.suppress(ValueError):
                    err.retry_after = float(retry_after)  # type: ignore[attr-defined]
            raise err

        if response.status_code != 200:
            raise ApiError(
                f"GraphQL request failed with status {response.status_code}",
                status_code=response.status_code,
            )

        body = response.json()
        if "errors" in body:
            messages = "; ".join(e.get("message", str(e)) for e in body["errors"])
            raise ApiError(f"GraphQL error: {messages}")

        return body.get("data", {})

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GraphQLClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
