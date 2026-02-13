"""Business logic for container registry authentication."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient


class RegistryService:
    """Manage RunPod container registry credentials."""

    def __init__(self, client: RestClient):
        self._client = client

    def create(self, name: str, username: str, password: str) -> dict[str, Any]:
        """Create a new container registry auth."""
        return self._client.create_registry_auth(name, username, password)

    def update(self, registry_auth_id: str, username: str, password: str) -> dict[str, Any]:
        """Update registry auth credentials."""
        return self._client.update_registry_auth(registry_auth_id, username, password)

    def delete(self, registry_auth_id: str) -> dict[str, Any]:
        """Delete a registry auth entry."""
        return self._client.delete_registry_auth(registry_auth_id)
