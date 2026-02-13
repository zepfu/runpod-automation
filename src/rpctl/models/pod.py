"""Pydantic models for RunPod pods."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Pod(BaseModel):
    """A RunPod GPU/CPU pod."""

    id: str
    name: str = ""
    image_name: str = ""
    status: str = ""  # RUNNING, EXITED, etc.
    desired_status: str = ""
    gpu_type: str = ""
    gpu_count: int = 0
    vcpu_count: int = 0
    memory_mb: int = 0
    container_disk_gb: int = 0
    volume_disk_gb: int = 0
    volume_mount_path: str = ""
    cost_per_hr: float = 0.0
    machine_id: str = ""
    cloud_type: str = ""
    ports: str = ""
    runtime: dict[str, Any] = Field(default_factory=dict)
    env: list[dict[str, str]] = Field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Pod:
        """Parse from RunPod SDK pod response."""
        runtime = data.get("runtime") or {}
        machine = data.get("machine") or {}
        gpu_type = machine.get("gpuDisplayName", "")
        if not gpu_type:
            gpu_type = data.get("gpuTypeId", data.get("gpu", ""))

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image_name=data.get("imageName", ""),
            status=runtime.get("status", data.get("desiredStatus", "")),
            desired_status=data.get("desiredStatus", ""),
            gpu_type=gpu_type,
            gpu_count=data.get("gpuCount", 0),
            vcpu_count=data.get("vcpu", 0),
            memory_mb=data.get("memoryInGb", 0) * 1024 if data.get("memoryInGb") else 0,
            container_disk_gb=data.get("containerDiskInGb", 0),
            volume_disk_gb=data.get("volumeInGb", 0),
            volume_mount_path=data.get("volumeMountPath", ""),
            cost_per_hr=data.get("costPerHr", 0.0),
            machine_id=data.get("machineId", machine.get("id", "")),
            cloud_type=data.get("cloudType", ""),
            ports=data.get("port", data.get("ports", "")),
            runtime=runtime,
            env=data.get("env", []),
        )


class PodCreateParams(BaseModel):
    """Parameters for creating a pod."""

    name: str = "rpctl-pod"
    image_name: str
    gpu_type_id: str | None = None
    gpu_type_ids: list[str] = Field(default_factory=list)
    gpu_count: int = 1
    cloud_type: str = "SECURE"
    compute_type: str = "GPU"
    cpu_flavor_ids: list[str] = Field(default_factory=list)
    container_disk_in_gb: int = 50
    volume_in_gb: int = 20
    volume_mount_path: str = "/workspace"
    network_volume_id: str | None = None
    ports: str = "8888/http,22/tcp"
    env: dict[str, str] = Field(default_factory=dict)
    docker_entrypoint: str | None = None
    docker_start_cmd: str | None = None
    template_id: str | None = None
    min_vcpu_per_gpu: int = 2
    min_ram_per_gpu: int = 8
    data_center_ids: list[str] = Field(default_factory=list)
    interruptible: bool = False
    allowed_cuda_versions: list[str] = Field(default_factory=list)
    support_public_ip: bool = False

    def to_sdk_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs for runpod.create_pod()."""
        kwargs: dict[str, Any] = {
            "name": self.name,
            "image_name": self.image_name,
            "gpu_count": self.gpu_count,
            "cloud_type": self.cloud_type,
            "container_disk_in_gb": self.container_disk_in_gb,
            "volume_in_gb": self.volume_in_gb,
            "volume_mount_path": self.volume_mount_path,
            "ports": self.ports,
            "min_vcpu_count": self.min_vcpu_per_gpu,
            "min_memory_in_gb": self.min_ram_per_gpu,
        }
        if self.gpu_type_id:
            kwargs["gpu_type_id"] = self.gpu_type_id
        if self.gpu_type_ids:
            kwargs["gpu_type_ids"] = self.gpu_type_ids
        if self.network_volume_id:
            kwargs["network_volume_id"] = self.network_volume_id
        if self.env:
            kwargs["env"] = self.env
        if self.docker_entrypoint:
            kwargs["docker_args"] = self.docker_entrypoint
        if self.template_id:
            kwargs["template_id"] = self.template_id
        if self.data_center_ids:
            kwargs["data_center_id"] = self.data_center_ids[0]
        if self.interruptible:
            kwargs["bid_per_gpu"] = 0.0  # Will use market rate
        if self.support_public_ip:
            kwargs["support_public_ip"] = True
        return kwargs
