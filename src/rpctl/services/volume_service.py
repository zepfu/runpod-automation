"""Business logic for network volume management."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient
from rpctl.models.volume import Volume


class VolumeService:
    """Manage RunPod network volumes."""

    def __init__(self, client: RestClient):
        self._client = client

    def list_volumes(self) -> list[Volume]:
        """List all network volumes."""
        raw = self._client.get_volumes()
        return [Volume.from_api(v) for v in raw]

    def get_volume(self, volume_id: str) -> Volume:
        """Get a single volume by ID."""
        raw = self._client.get_volume(volume_id)
        return Volume.from_api(raw)

    def create_volume(self, name: str, size_gb: int, data_center_id: str) -> Volume:
        """Create a new network volume."""
        raw = self._client.create_volume(name=name, size=size_gb, data_center_id=data_center_id)
        return Volume.from_api(raw)

    def update_volume(self, volume_id: str, **kwargs: Any) -> Volume:
        """Update an existing volume (name, size)."""
        raw = self._client.update_volume(volume_id, **kwargs)
        return Volume.from_api(raw)

    def delete_volume(self, volume_id: str) -> dict[str, Any]:
        """Delete a network volume."""
        return self._client.delete_volume(volume_id)
