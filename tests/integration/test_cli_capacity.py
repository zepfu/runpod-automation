"""Integration tests for capacity CLI commands."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from rpctl.main import app
from rpctl.models.capacity import (
    Datacenter,
    DatacenterGpu,
    GpuAvailabilityDetail,
    GpuPricing,
    GpuStock,
    GpuType,
)
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def mock_capacity_service():
    """Mock the CapacityService and Settings for CLI tests."""
    gpu_types = [
        GpuType(
            id="NVIDIA GeForce RTX 4090",
            display_name="NVIDIA GeForce RTX 4090",
            memory_gb=24,
            secure_cloud=True,
            community_cloud=True,
            pricing=GpuPricing(
                secure_price=0.44,
                community_price=0.34,
                min_bid_price=0.29,
                on_demand_price=0.34,
            ),
            stock=GpuStock(
                stock_status="High",
                max_unreserved=50,
                total_count=200,
            ),
        ),
        GpuType(
            id="NVIDIA A100 80GB PCIe",
            display_name="NVIDIA A100 80GB PCIe",
            memory_gb=80,
            secure_cloud=True,
            community_cloud=True,
            pricing=GpuPricing(
                secure_price=1.64,
                on_demand_price=1.24,
            ),
            stock=GpuStock(stock_status="Low", max_unreserved=5),
        ),
    ]

    detail = GpuAvailabilityDetail(
        id="NVIDIA GeForce RTX 4090",
        display_name="NVIDIA GeForce RTX 4090",
        memory_gb=24,
        pricing=GpuPricing(on_demand_price=0.34, min_bid_price=0.29),
        stock=GpuStock(stock_status="High", total_count=200, rented_count=150, max_unreserved=50),
    )

    datacenters = [
        Datacenter(
            id="US-TX-3",
            name="US Texas 3",
            location="Dallas, TX",
            region="NORTH_AMERICA",
            storage_support=True,
            gpus=[
                DatacenterGpu(
                    gpu_type_id="NVIDIA GeForce RTX 4090",
                    display_name="NVIDIA GeForce RTX 4090",
                    available=True,
                    stock_status="High",
                ),
            ],
        ),
    ]

    mock_svc = MagicMock()
    mock_svc.list_gpu_types.return_value = gpu_types
    mock_svc.check_gpu.return_value = detail
    mock_svc.list_regions.return_value = datacenters

    mock_settings = MagicMock()
    mock_settings.api_key = "test-key"

    return mock_svc, mock_settings


def _patch_capacity(mock_svc, mock_settings):
    """Return context managers that patch the capacity CLI's lazy imports."""
    return (
        patch("rpctl.config.settings.Settings.load", return_value=mock_settings),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    )


def test_capacity_list_table(mock_capacity_service):
    mock_svc, mock_settings = mock_capacity_service
    p1, p2, p3 = _patch_capacity(mock_svc, mock_settings)
    with p1, p2, p3:
        result = runner.invoke(app, ["capacity", "list"])
        assert result.exit_code == 0
        assert "RTX 4090" in result.output
        assert "A100" in result.output


def test_capacity_list_json(mock_capacity_service):
    mock_svc, mock_settings = mock_capacity_service
    p1, p2, p3 = _patch_capacity(mock_svc, mock_settings)
    with p1, p2, p3:
        result = runner.invoke(app, ["--json", "capacity", "list"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["id"] == "NVIDIA GeForce RTX 4090"


def test_capacity_check(mock_capacity_service):
    mock_svc, mock_settings = mock_capacity_service
    p1, p2, p3 = _patch_capacity(mock_svc, mock_settings)
    with p1, p2, p3:
        result = runner.invoke(app, ["capacity", "check", "--gpu", "NVIDIA GeForce RTX 4090"])
        assert result.exit_code == 0
        assert "RTX 4090" in result.output


def test_capacity_regions(mock_capacity_service):
    mock_svc, mock_settings = mock_capacity_service
    p1, p2, p3 = _patch_capacity(mock_svc, mock_settings)
    with p1, p2, p3:
        result = runner.invoke(app, ["capacity", "regions"])
        assert result.exit_code == 0
        assert "US-TX-3" in result.output
