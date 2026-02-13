"""Business logic for serverless endpoint management."""

from __future__ import annotations

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

    def update_endpoint(self, endpoint_id: str, **kwargs) -> Endpoint:
        """Update an existing endpoint."""
        raw = self._client.update_endpoint(endpoint_id, **kwargs)
        return Endpoint.from_api(raw)

    def delete_endpoint(self, endpoint_id: str) -> dict:
        """Delete an endpoint."""
        return self._client.delete_endpoint(endpoint_id)
