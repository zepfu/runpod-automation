"""Business logic for secrets management."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient


class SecretService:
    """Manage RunPod environment secrets."""

    def __init__(self, client: RestClient):
        self._client = client

    def list_secrets(self) -> list[dict[str, Any]]:
        """List all secrets."""
        return self._client.get_secrets()

    def set_secret(self, name: str, value: str) -> dict[str, Any]:
        """Create or update a secret."""
        return self._client.add_secret(name, value)

    def delete_secret(self, name: str) -> dict[str, Any]:
        """Delete a secret by name."""
        return self._client.delete_secret(name)
