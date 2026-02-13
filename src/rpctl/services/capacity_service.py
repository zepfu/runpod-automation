"""Business logic for GPU/CPU capacity queries."""

from __future__ import annotations

from rpctl.api.graphql_client import GraphQLClient
from rpctl.api.queries import (
    CPU_TYPES_LIST,
    DATACENTER_AVAILABILITY,
    GPU_TYPE_AVAILABILITY,
    GPU_TYPES_LIST,
)
from rpctl.models.capacity import CpuType, Datacenter, GpuAvailabilityDetail, GpuType


class CapacityService:
    """Query and filter GPU/CPU availability and pricing."""

    def __init__(self, graphql: GraphQLClient):
        self._gql = graphql

    def list_gpu_types(
        self,
        cloud_type: str = "all",
        min_vram: int | None = None,
        available_only: bool = False,
        sort_by: str = "price",
    ) -> list[GpuType]:
        """List all GPU types with pricing and stock info."""
        data = self._gql.execute(GPU_TYPES_LIST)
        raw_types = data.get("gpuTypes") or []
        gpu_types = [GpuType.from_api(g) for g in raw_types]

        # Filter by cloud type
        if cloud_type == "secure":
            gpu_types = [g for g in gpu_types if g.secure_cloud]
        elif cloud_type == "community":
            gpu_types = [g for g in gpu_types if g.community_cloud]

        # Filter by VRAM
        if min_vram:
            gpu_types = [g for g in gpu_types if g.memory_gb >= min_vram]

        # Filter by availability
        if available_only:
            gpu_types = [
                g
                for g in gpu_types
                if g.stock.stock_status and g.stock.stock_status.lower() != "unavailable"
            ]

        # Sort
        sort_keys = {
            "price": lambda g: g.pricing.on_demand_price or float("inf"),
            "vram": lambda g: -(g.memory_gb or 0),
            "name": lambda g: g.display_name.lower(),
            "availability": lambda g: -(g.stock.total_count or 0),
        }
        key_fn = sort_keys.get(sort_by, sort_keys["price"])
        gpu_types.sort(key=key_fn)

        return gpu_types

    def check_gpu(
        self,
        gpu_type: str,
        gpu_count: int = 1,
        cloud_type: str = "secure",
    ) -> GpuAvailabilityDetail:
        """Check availability for a specific GPU type."""
        data = self._gql.execute(
            GPU_TYPE_AVAILABILITY,
            {
                "gpuTypeId": gpu_type,
                "gpuCount": gpu_count,
                "secureCloud": cloud_type == "secure",
            },
        )
        raw_types = data.get("gpuTypes") or []
        if not raw_types:
            from rpctl.errors import ResourceNotFoundError

            raise ResourceNotFoundError(f"GPU type '{gpu_type}' not found.")
        return GpuAvailabilityDetail.from_api(raw_types[0])

    def list_regions(self, gpu_filter: str | None = None) -> list[Datacenter]:
        """List all datacenters with GPU availability."""
        data = self._gql.execute(DATACENTER_AVAILABILITY)
        myself = data.get("myself") or {}
        raw_dcs = myself.get("datacenters") or []
        datacenters = [Datacenter.from_api(dc) for dc in raw_dcs]

        if gpu_filter:
            gpu_lower = gpu_filter.lower()
            datacenters = [
                dc
                for dc in datacenters
                if any(
                    gpu_lower in g.gpu_type_id.lower() or gpu_lower in g.display_name.lower()
                    for g in dc.gpus
                )
            ]

        datacenters.sort(key=lambda dc: dc.id)
        return datacenters

    def list_cpu_types(self) -> list[CpuType]:
        """List all CPU types."""
        data = self._gql.execute(CPU_TYPES_LIST)
        raw_types = data.get("cpuTypes") or []
        return [CpuType.from_api(c) for c in raw_types]
