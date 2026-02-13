"""Pydantic models for GPU/CPU capacity and availability data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GpuPricing(BaseModel):
    """Pricing info for a GPU type."""

    secure_price: float | None = None
    community_price: float | None = None
    secure_spot_price: float | None = None
    community_spot_price: float | None = None
    min_bid_price: float | None = None
    on_demand_price: float | None = None


class GpuStock(BaseModel):
    """Stock/availability info for a GPU type."""

    stock_status: str | None = None
    rented_count: int | None = None
    total_count: int | None = None
    rental_percentage: float | None = None
    max_unreserved: int | None = None
    available_counts: list[int] = Field(default_factory=list)


class GpuType(BaseModel):
    """A GPU type with pricing and availability."""

    id: str
    display_name: str
    manufacturer: str | None = None
    memory_gb: int = 0
    cuda_cores: int | None = None
    secure_cloud: bool = False
    community_cloud: bool = False
    max_gpu_count: int | None = None
    pricing: GpuPricing = Field(default_factory=GpuPricing)
    stock: GpuStock = Field(default_factory=GpuStock)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> GpuType:
        """Parse from GraphQL gpuTypes response."""
        lowest = data.get("lowestPrice") or {}
        return cls(
            id=data.get("id", ""),
            display_name=data.get("displayName", data.get("id", "")),
            manufacturer=data.get("manufacturer"),
            memory_gb=data.get("memoryInGb", 0),
            cuda_cores=data.get("cudaCores"),
            secure_cloud=data.get("secureCloud", False),
            community_cloud=data.get("communityCloud", False),
            max_gpu_count=data.get("maxGpuCount"),
            pricing=GpuPricing(
                secure_price=data.get("securePrice"),
                community_price=data.get("communityPrice"),
                secure_spot_price=data.get("secureSpotPrice"),
                community_spot_price=data.get("communitySpotPrice"),
                min_bid_price=lowest.get("minimumBidPrice"),
                on_demand_price=lowest.get("uninterruptablePrice"),
            ),
            stock=GpuStock(
                stock_status=lowest.get("stockStatus"),
                rented_count=lowest.get("rentedCount"),
                total_count=lowest.get("totalCount"),
                rental_percentage=lowest.get("rentalPercentage"),
                max_unreserved=lowest.get("maxUnreservedGpuCount"),
                available_counts=lowest.get("availableGpuCounts") or [],
            ),
        )


class GpuAvailabilityDetail(BaseModel):
    """Detailed availability info for a GPU check command."""

    id: str
    display_name: str
    memory_gb: int = 0
    pricing: GpuPricing = Field(default_factory=GpuPricing)
    stock: GpuStock = Field(default_factory=GpuStock)
    country_code: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> GpuAvailabilityDetail:
        """Parse from GraphQL gpuTypes availability response."""
        lowest = data.get("lowestPrice") or {}
        return cls(
            id=data.get("id", ""),
            display_name=data.get("displayName", data.get("id", "")),
            memory_gb=data.get("memoryInGb", 0),
            pricing=GpuPricing(
                secure_price=data.get("securePrice"),
                community_price=data.get("communityPrice"),
                secure_spot_price=data.get("secureSpotPrice"),
                community_spot_price=data.get("communitySpotPrice"),
                min_bid_price=lowest.get("minimumBidPrice"),
                on_demand_price=lowest.get("uninterruptablePrice"),
            ),
            stock=GpuStock(
                stock_status=lowest.get("stockStatus"),
                rented_count=lowest.get("rentedCount"),
                total_count=lowest.get("totalCount"),
                rental_percentage=lowest.get("rentalPercentage"),
                max_unreserved=lowest.get("maxUnreservedGpuCount"),
                available_counts=lowest.get("availableGpuCounts") or [],
            ),
            country_code=lowest.get("countryCode"),
        )


class DatacenterGpu(BaseModel):
    """GPU availability within a specific datacenter."""

    gpu_type_id: str
    display_name: str
    available: bool = False
    stock_status: str | None = None


class Datacenter(BaseModel):
    """A RunPod datacenter with GPU availability."""

    id: str
    name: str | None = None
    location: str | None = None
    region: str | None = None
    storage_support: bool = False
    gpus: list[DatacenterGpu] = Field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Datacenter:
        """Parse from GraphQL myself.datacenters response."""
        gpu_avail = data.get("gpuAvailability") or []
        gpus = [
            DatacenterGpu(
                gpu_type_id=g.get("gpuTypeId", ""),
                display_name=g.get("gpuTypeDisplayName", ""),
                available=g.get("available", False),
                stock_status=g.get("stockStatus"),
            )
            for g in gpu_avail
        ]
        return cls(
            id=data.get("id", ""),
            name=data.get("name"),
            location=data.get("location"),
            region=data.get("region"),
            storage_support=data.get("storageSupport", False),
            gpus=gpus,
        )


class CpuType(BaseModel):
    """A CPU type."""

    id: str
    display_name: str
    manufacturer: str | None = None
    cores: int | None = None
    threads_per_core: int | None = None
    group_id: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> CpuType:
        return cls(
            id=data.get("id", ""),
            display_name=data.get("displayName", data.get("id", "")),
            manufacturer=data.get("manufacturer"),
            cores=data.get("cores"),
            threads_per_core=data.get("threadsPerCore"),
            group_id=data.get("groupId"),
        )
