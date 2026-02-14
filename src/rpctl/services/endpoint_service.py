"""Business logic for serverless endpoint management."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient
from rpctl.models.endpoint import Endpoint, EndpointCreateParams


class EndpointService:
    """Manage RunPod serverless endpoints."""

    def __init__(self, client: RestClient):
        self._client = client

    def list_endpoints(self) -> list[Endpoint]:
        """List all serverless endpoints."""
        raw = self._client.get_endpoints()
        return [Endpoint.from_api(e) for e in raw]

    def get_endpoint(self, endpoint_id: str) -> Endpoint:
        """Get a single endpoint by ID."""
        raw = self._client.get_endpoint(endpoint_id)
        return Endpoint.from_api(raw)

    def create_endpoint(self, params: EndpointCreateParams) -> Endpoint:
        """Create a new serverless endpoint."""
        raw = self._client.create_endpoint(**params.to_sdk_kwargs())
        return Endpoint.from_api(raw)

    def update_endpoint(self, endpoint_id: str, **kwargs: Any) -> Endpoint:
        """Update an existing endpoint."""
        raw = self._client.update_endpoint(endpoint_id, **kwargs)
        return Endpoint.from_api(raw)

    def delete_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        """Delete an endpoint."""
        return self._client.delete_endpoint(endpoint_id)

    def health(self, endpoint_id: str) -> dict[str, Any]:
        """Get endpoint health status (workers, jobs, queue)."""
        return self._client.endpoint_health(endpoint_id)

    def run_sync(
        self, endpoint_id: str, request_input: dict[str, Any], timeout: int = 86400
    ) -> dict[str, Any]:
        """Run a synchronous job on the endpoint."""
        return self._client.endpoint_run_sync(endpoint_id, request_input, timeout)

    def run_async(self, endpoint_id: str, request_input: dict[str, Any]) -> str:
        """Submit an async job, return job ID."""
        return self._client.endpoint_run_async(endpoint_id, request_input)

    def purge_queue(self, endpoint_id: str) -> dict[str, Any]:
        """Purge the endpoint's job queue."""
        return self._client.endpoint_purge_queue(endpoint_id)

    def job_status(self, endpoint_id: str, job_id: str) -> dict[str, Any]:
        """Get the status of a specific job."""
        return self._client.endpoint_job_status(endpoint_id, job_id)

    def job_cancel(self, endpoint_id: str, job_id: str) -> dict[str, Any]:
        """Cancel a running or queued job."""
        return self._client.endpoint_job_cancel(endpoint_id, job_id)

    def stream(self, endpoint_id: str, job_id: str) -> list[dict[str, Any]]:
        """Stream output from a running job."""
        return self._client.endpoint_stream(endpoint_id, job_id)

    def wait_until_ready(
        self,
        endpoint_id: str,
        *,
        timeout: float = 300,
        interval: float = 5,
    ) -> dict[str, Any]:
        """Poll until endpoint has ready workers or timeout."""
        from rpctl.services.poll import poll_until

        result: dict[str, Any] = {}

        def check() -> tuple[bool, str]:
            nonlocal result
            health = self.health(endpoint_id)
            result = health
            workers = health.get("workers", {})
            ready = workers.get("ready", 0) if isinstance(workers, dict) else 0
            idle = workers.get("idle", 0) if isinstance(workers, dict) else 0
            total = ready + idle
            done = total > 0
            return done, f"workers ready={ready} idle={idle}"

        poll_until(check, timeout=timeout, interval=interval, label=f"endpoint {endpoint_id}")
        return result
