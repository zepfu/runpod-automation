"""Pydantic models for RunPod templates."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Template(BaseModel):
    """A RunPod template."""

    id: str
    name: str = ""
    image_name: str = ""
    container_disk_gb: int = 0
    volume_gb: int = 0
    volume_mount_path: str = ""
    ports: str = ""
    is_serverless: bool = False
    is_public: bool = False
    env: list[dict[str, str]] = Field(default_factory=list)
    category: str = ""
    readme: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Template:
        """Parse from RunPod API template response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image_name=data.get("imageName", ""),
            container_disk_gb=data.get("containerDiskInGb", 0),
            volume_gb=data.get("volumeInGb", 0),
            volume_mount_path=data.get("volumeMountPath", ""),
            ports=data.get("ports", ""),
            is_serverless=data.get("isServerless", False),
            is_public=data.get("isPublic", False),
            env=data.get("env", []),
            category=data.get("category", ""),
            readme=data.get("readme", ""),
        )
