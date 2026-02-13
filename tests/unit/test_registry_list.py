"""Tests for registry list command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import ApiError
from rpctl.services.registry_service import RegistryService

runner = CliRunner()


class TestRegistryServiceList:
    def test_list(self):
        client = MagicMock()
        client.list_registry_auths.return_value = [
            {"id": "reg-1", "name": "docker-hub"},
            {"id": "reg-2", "name": "ghcr"},
        ]
        svc = RegistryService(client)
        result = svc.list()
        assert len(result) == 2
        assert result[0]["name"] == "docker-hub"

    def test_list_empty(self):
        client = MagicMock()
        client.list_registry_auths.return_value = []
        svc = RegistryService(client)
        result = svc.list()
        assert result == []


class TestRegistryListCLI:
    @patch("rpctl.cli.registry._get_registry_service")
    def test_list_table(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list.return_value = [
            {"id": "reg-1", "name": "docker-hub"},
        ]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["registry", "list"])
        assert result.exit_code == 0
        assert "docker-hub" in result.output

    @patch("rpctl.cli.registry._get_registry_service")
    def test_list_json(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list.return_value = [
            {"id": "reg-1", "name": "docker-hub"},
        ]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["--output", "json", "registry", "list"])
        assert result.exit_code == 0

    @patch("rpctl.cli.registry._get_registry_service")
    def test_list_empty(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list.return_value = []
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["registry", "list"])
        assert result.exit_code == 0
        assert "No container registry" in result.output

    @patch("rpctl.cli.registry._get_registry_service")
    def test_list_error(self, mock_svc_fn):
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.list.side_effect = ApiError("Network error")
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["registry", "list"])
        assert result.exit_code != 0
