"""Business logic for pod management."""

from __future__ import annotations

from rpctl.api.rest_client import RestClient
from rpctl.models.pod import Pod, PodCreateParams


class PodService:
    """Manage RunPod GPU/CPU pods."""

    def __init__(self, client: RestClient):
        self._client = client

    def list_pods(self, status_filter: str | None = None) -> list[Pod]:
        """List all pods, optionally filtered by status."""
        raw = self._client.get_pods()
        pods = [Pod.from_api(p) for p in raw]
        if status_filter and status_filter != "all":
            pods = [p for p in pods if p.status.lower() == status_filter.lower()]
        return pods

    def get_pod(self, pod_id: str) -> Pod:
        """Get a single pod by ID."""
        raw = self._client.get_pod(pod_id)
        return Pod.from_api(raw)

    def create_pod(self, params: PodCreateParams) -> Pod:
        """Create a new pod."""
        raw = self._client.create_pod(**params.to_sdk_kwargs())
        return Pod.from_api(raw)

    def stop_pod(self, pod_id: str) -> dict:
        """Stop a running pod."""
        return self._client.stop_pod(pod_id)

    def start_pod(self, pod_id: str) -> dict:
        """Start/resume a stopped pod."""
        return self._client.resume_pod(pod_id)

    def restart_pod(self, pod_id: str) -> dict:
        """Restart a pod (stop then start)."""
        self._client.stop_pod(pod_id)
        return self._client.resume_pod(pod_id)

    def delete_pod(self, pod_id: str) -> dict:
        """Terminate and delete a pod."""
        return self._client.terminate_pod(pod_id)
