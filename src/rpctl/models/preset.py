"""Pydantic models for rpctl presets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class PresetMetadata(BaseModel):
    """Metadata about a saved preset."""

    name: str
    resource_type: Literal["pod", "endpoint"]
    description: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    source: str = ""  # e.g. "from-pod:pod-abc123", "cli"


class Preset(BaseModel):
    """A saved preset that pre-fills create command parameters."""

    metadata: PresetMetadata
    params: dict[str, Any] = Field(default_factory=dict)
