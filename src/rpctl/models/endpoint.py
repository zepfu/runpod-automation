"""Pydantic models for RunPod serverless endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Endpoint(BaseModel):
    """A RunPod serverless endpoint."""

    id: str
    name: str = ""
    template_id: str = ""
    gpu_ids: str = ""
    gpu_count: int = 0
    workers_min: int = 0
    workers_max: int = 0
    workers_current: int = 0
    idle_timeout: int = 5
    locations: str = ""
    network_volume_id: str | None = None
    scaler_type: str = ""
    scaler_value: int = 0
    flashboot: bool = False
    queue_delay: int = 0
    jobs_in_progress: int = 0
    jobs_completed: int = 0
    workers_ready: int = 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Endpoint:
        """Parse from RunPod API endpoint response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            template_id=data.get("templateId", ""),
            gpu_ids=data.get("gpuIds", data.get("gpuTypeIds", "")),
            gpu_count=data.get("gpuCount", 0),
            workers_min=data.get("workersMin", 0),
            workers_max=data.get("workersMax", 0),
            workers_current=data.get("workersCurrent", data.get("workersRunning", 0)),
            idle_timeout=data.get("idleTimeout", 5),
            locations=data.get("locations", data.get("dataCenterIds", "")),
            network_volume_id=data.get("networkVolumeId"),
            scaler_type=data.get("scalerType", ""),
            scaler_value=data.get("scalerValue", 0),
            flashboot=data.get("flashboot", False),
            queue_delay=data.get("queueDelay", 0),
            jobs_in_progress=data.get("jobsInProgress", 0),
            jobs_completed=data.get("jobsCompleted", 0),
            workers_ready=data.get("workersReady", 0),
        )


class EndpointCreateParams(BaseModel):
    """Parameters for creating a serverless endpoint."""

    name: str
    template_id: str
    gpu_ids: str = "AMPERE_24"
    gpu_count: int = 1
    workers_min: int = 0
    workers_max: int = 3
    idle_timeout: int = 5
    scaler_type: str = "QUEUE_DELAY"
    scaler_value: int = 4
    network_volume_id: str | None = None
    flashboot: bool = False
    locations: str = ""
    allowed_cuda_versions: list[str] | None = None

    def to_sdk_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for runpod.create_endpoint()."""
        kwargs: dict[str, Any] = {
            "name": self.name,
            "template_id": self.template_id,
            "gpu_ids": self.gpu_ids,
            "workers_min": self.workers_min,
            "workers_max": self.workers_max,
            "idle_timeout": self.idle_timeout,
            "scaler_type": self.scaler_type,
            "scaler_value": self.scaler_value,
        }
        if self.network_volume_id:
            kwargs["network_volume_id"] = self.network_volume_id
        if self.flashboot:
            kwargs["flashboot"] = True
        if self.locations:
            kwargs["locations"] = self.locations
        if self.allowed_cuda_versions:
            kwargs["allowed_cuda_versions"] = ",".join(self.allowed_cuda_versions)
        return kwargs
