"""Unit tests for capacity service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from rpctl.errors import ResourceNotFoundError
from rpctl.services.capacity_service import CapacityService


@pytest.fixture
def mock_graphql(gpu_types_response, datacenter_response):
    client = MagicMock()

    def execute_side_effect(query, variables=None):
        if "gpuTypes" in query and variables and "gpuTypeId" in variables:
            # Simulate check query — return matching GPU type
            gpu_id = variables["gpuTypeId"]
            matching = [g for g in gpu_types_response["gpuTypes"] if g["id"] == gpu_id]
            return {"gpuTypes": matching}
        if "gpuTypes" in query:
            return gpu_types_response
        if "myself" in query:
            return datacenter_response
        return {}

    client.execute.side_effect = execute_side_effect
    return client


class TestListGpuTypes:
    def test_returns_all(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types()
        assert len(result) == 4

    def test_filter_secure(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(cloud_type="secure")
        assert all(g.secure_cloud for g in result)
        # Tesla T4 is community only
        assert not any(g.id == "Tesla T4" for g in result)

    def test_filter_community(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(cloud_type="community")
        assert all(g.community_cloud for g in result)
        # H100 is secure only
        assert not any(g.id == "NVIDIA H100 80GB HBM3" for g in result)

    def test_filter_min_vram(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(min_vram=48)
        assert all(g.memory_gb >= 48 for g in result)
        assert len(result) == 2  # A100 80GB and H100 80GB

    def test_sort_by_price(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(sort_by="price")
        prices = [g.pricing.on_demand_price or float("inf") for g in result]
        assert prices == sorted(prices)

    def test_sort_by_vram(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(sort_by="vram")
        vrams = [g.memory_gb for g in result]
        assert vrams == sorted(vrams, reverse=True)

    def test_sort_by_name(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_gpu_types(sort_by="name")
        names = [g.display_name.lower() for g in result]
        assert names == sorted(names)


class TestCheckGpu:
    def test_returns_detail(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        detail = svc.check_gpu("NVIDIA GeForce RTX 4090")
        assert detail.id == "NVIDIA GeForce RTX 4090"
        assert detail.stock.stock_status == "High"

    def test_not_found_raises(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        with pytest.raises(ResourceNotFoundError, match="not found"):
            svc.check_gpu("NONEXISTENT GPU")


class TestListRegions:
    def test_returns_all(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_regions()
        assert len(result) == 3

    def test_sorted_by_id(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_regions()
        ids = [dc.id for dc in result]
        assert ids == sorted(ids)

    def test_filter_by_gpu(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_regions(gpu_filter="H100")
        assert len(result) == 1
        assert result[0].id == "CA-MTL-1"

    def test_filter_by_gpu_case_insensitive(self, mock_graphql):
        svc = CapacityService(mock_graphql)
        result = svc.list_regions(gpu_filter="rtx 4090")
        assert len(result) == 2  # US-TX-3 and EU-RO-1
