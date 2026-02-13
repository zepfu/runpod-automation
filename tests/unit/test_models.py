"""Unit tests for Pydantic models."""

from __future__ import annotations

from rpctl.models.capacity import CpuType, Datacenter, GpuAvailabilityDetail, GpuType


class TestGpuType:
    def test_from_api_full(self, gpu_types_response):
        raw = gpu_types_response["gpuTypes"][0]
        gpu = GpuType.from_api(raw)
        assert gpu.id == "NVIDIA GeForce RTX 4090"
        assert gpu.memory_gb == 24
        assert gpu.secure_cloud is True
        assert gpu.community_cloud is True
        assert gpu.pricing.secure_price == 0.44
        assert gpu.pricing.community_price == 0.34
        assert gpu.pricing.min_bid_price == 0.29
        assert gpu.stock.stock_status == "High"
        assert gpu.stock.rented_count == 150
        assert gpu.stock.total_count == 200
        assert gpu.stock.max_unreserved == 50

    def test_from_api_missing_lowest_price(self):
        raw = {
            "id": "test-gpu",
            "displayName": "Test GPU",
            "memoryInGb": 16,
        }
        gpu = GpuType.from_api(raw)
        assert gpu.id == "test-gpu"
        assert gpu.pricing.on_demand_price is None
        assert gpu.stock.stock_status is None

    def test_from_api_all_types(self, gpu_types_response):
        for raw in gpu_types_response["gpuTypes"]:
            gpu = GpuType.from_api(raw)
            assert gpu.id
            assert gpu.memory_gb > 0


class TestGpuAvailabilityDetail:
    def test_from_api(self, gpu_types_response):
        raw = gpu_types_response["gpuTypes"][1]
        detail = GpuAvailabilityDetail.from_api(raw)
        assert detail.id == "NVIDIA A100 80GB PCIe"
        assert detail.memory_gb == 80
        assert detail.stock.stock_status == "Low"


class TestDatacenter:
    def test_from_api(self, datacenter_response):
        raw = datacenter_response["myself"]["datacenters"][0]
        dc = Datacenter.from_api(raw)
        assert dc.id == "US-TX-3"
        assert dc.name == "US Texas 3"
        assert dc.storage_support is True
        assert len(dc.gpus) == 2
        assert dc.gpus[0].available is True
        assert dc.gpus[0].gpu_type_id == "NVIDIA GeForce RTX 4090"

    def test_from_api_all(self, datacenter_response):
        for raw in datacenter_response["myself"]["datacenters"]:
            dc = Datacenter.from_api(raw)
            assert dc.id


class TestCpuType:
    def test_from_api(self):
        raw = {
            "id": "cpu5c",
            "displayName": "CPU 5C",
            "manufacturer": "AMD",
            "cores": 32,
            "threadsPerCore": 2,
            "groupId": "group-a",
        }
        cpu = CpuType.from_api(raw)
        assert cpu.id == "cpu5c"
        assert cpu.cores == 32
        assert cpu.threads_per_core == 2
