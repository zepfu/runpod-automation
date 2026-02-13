"""Pydantic models for RunPod network volumes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Volume(BaseModel):
    """A RunPod network volume."""

    id: str
    name: str = ""
    size_gb: int = 0
    data_center_id: str = ""
    used_size_gb: float = 0.0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Volume:
        """Parse from RunPod API volume response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            size_gb=data.get("size", data.get("sizeInGb", 0)),
            data_center_id=data.get("dataCenterId", ""),
            used_size_gb=data.get("usedSize", 0.0),
        )
