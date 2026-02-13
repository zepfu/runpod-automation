"""Tests for capacity cpus command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.models.capacity import CpuType
from rpctl.services.capacity_service import CapacityService

runner = CliRunner()


class TestCapacityServiceCpus:
    def test_list_cpu_types(self):
        """Service returns parsed CpuType objects."""
        mock_gql = MagicMock()
        mock_gql.execute.return_value = {
            "cpuTypes": [
                {
                    "id": "cpu-1",
                    "displayName": "AMD EPYC 7B13",
                    "manufacturer": "AMD",
                    "cores": 64,
                    "threadsPerCore": 2,
                    "groupId": "epyc",
                },
                {
                    "id": "cpu-2",
                    "displayName": "Intel Xeon E5-2697A",
                    "manufacturer": "Intel",
                    "cores": 16,
                    "threadsPerCore": 2,
                    "groupId": "xeon",
                },
            ]
        }
        svc = CapacityService(mock_gql)
        result = svc.list_cpu_types()
        assert len(result) == 2
        assert result[0].id == "cpu-1"
        assert result[0].cores == 64
        assert result[1].manufacturer == "Intel"

    def test_list_cpu_types_empty(self):
        mock_gql = MagicMock()
        mock_gql.execute.return_value = {"cpuTypes": []}
        svc = CapacityService(mock_gql)
        result = svc.list_cpu_types()
        assert result == []


class TestCapacityCpusCLI:
    @patch("rpctl.cli.capacity._get_capacity_service")
    def test_cpus_table(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list_cpu_types.return_value = [
            CpuType(
                id="cpu-1",
                display_name="AMD EPYC 7B13",
                manufacturer="AMD",
                cores=64,
            ),
        ]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["capacity", "cpus"])
        assert result.exit_code == 0
        assert "AMD EPYC" in result.output

    @patch("rpctl.cli.capacity._get_capacity_service")
    def test_cpus_json(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list_cpu_types.return_value = [
            CpuType(id="cpu-1", display_name="AMD EPYC 7B13"),
        ]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["--output", "json", "capacity", "cpus"])
        assert result.exit_code == 0

    @patch("rpctl.cli.capacity._get_capacity_service")
    def test_cpus_empty(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list_cpu_types.return_value = []
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["capacity", "cpus"])
        assert result.exit_code == 0
        assert "No CPU types" in result.output

    @patch("rpctl.cli.capacity._get_capacity_service")
    def test_cpus_error(self, mock_svc_fn):
        from rpctl.errors import ApiError
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list_cpu_types.side_effect = ApiError("Network error")
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["capacity", "cpus"])
        assert result.exit_code != 0
