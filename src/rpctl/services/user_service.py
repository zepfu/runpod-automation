"""Business logic for user/account management."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient


class UserService:
    """Manage RunPod user settings."""

    def __init__(self, client: RestClient):
        self._client = client

    def get_info(self) -> dict[str, Any]:
        """Get current user info (account, SSH key, volumes)."""
        return self._client.get_user()

    def set_ssh_key(self, pubkey: str) -> dict[str, Any]:
        """Upload/update the user's SSH public key."""
        return self._client.update_user_settings(pubkey)
