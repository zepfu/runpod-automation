"""Business logic for template management."""

from __future__ import annotations

from typing import Any

from rpctl.api.rest_client import RestClient
from rpctl.models.template import Template


class TemplateService:
    """Manage RunPod templates."""

    def __init__(self, client: RestClient):
        self._client = client

    def list_templates(self) -> list[Template]:
        """List all templates."""
        raw = self._client.get_templates()
        return [Template.from_api(t) for t in raw]

    def get_template(self, template_id: str) -> Template:
        """Get a single template by ID."""
        raw = self._client.get_template(template_id)
        return Template.from_api(raw)

    def create_template(self, **kwargs: Any) -> Template:
        """Create a new template."""
        raw = self._client.create_template(**kwargs)
        return Template.from_api(raw)

    def update_template(self, template_id: str, **kwargs: Any) -> Template:
        """Update an existing template."""
        raw = self._client.update_template(template_id, **kwargs)
        return Template.from_api(raw)

    def delete_template(self, template_id: str) -> dict[str, Any]:
        """Delete a template."""
        return self._client.delete_template(template_id)
