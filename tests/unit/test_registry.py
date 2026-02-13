"""Tests for container registry auth — service layer and CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rpctl.errors import ApiError
from rpctl.main import app
from rpctl.services.registry_service import RegistryService
from typer.testing import CliRunner

runner = CliRunner()


# --- RegistryService ---


def test_registry_service_create():
    client = MagicMock()
    client.create_registry_auth.return_value = {"id": "reg-001", "name": "my-reg"}
    svc = RegistryService(client)
    result = svc.create("my-reg", "user", "pass")
    assert result == {"id": "reg-001", "name": "my-reg"}
    client.create_registry_auth.assert_called_once_with("my-reg", "user", "pass")


def test_registry_service_update():
    client = MagicMock()
    client.update_registry_auth.return_value = {"id": "reg-001", "name": "my-reg"}
    svc = RegistryService(client)
    result = svc.update("reg-001", "new-user", "new-pass")
    assert result == {"id": "reg-001", "name": "my-reg"}
    client.update_registry_auth.assert_called_once_with("reg-001", "new-user", "new-pass")


def test_registry_service_delete():
    client = MagicMock()
    client.delete_registry_auth.return_value = {}
    svc = RegistryService(client)
    result = svc.delete("reg-001")
    assert result == {}
    client.delete_registry_auth.assert_called_once_with("reg-001")


# --- CLI: registry create ---


def test_cli_registry_create():
    mock_svc = MagicMock()
    mock_svc.create.return_value = {"id": "reg-001", "name": "my-reg"}
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "create", "--name", "my-reg", "--username", "user"],
            input="password\n",
        )
        assert result.exit_code == 0
        mock_svc.create.assert_called_once_with("my-reg", "user", "password")


def test_cli_registry_create_api_error():
    mock_svc = MagicMock()
    mock_svc.create.side_effect = ApiError("boom", status_code=500)
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "create", "--name", "my-reg", "--username", "user"],
            input="password\n",
        )
        assert result.exit_code != 0


# --- CLI: registry update ---


def test_cli_registry_update():
    mock_svc = MagicMock()
    mock_svc.update.return_value = {"id": "reg-001", "name": "my-reg"}
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "update", "reg-001", "--username", "new-user"],
            input="password\n",
        )
        assert result.exit_code == 0
        mock_svc.update.assert_called_once_with("reg-001", "new-user", "password")


# --- CLI: registry delete ---


def test_cli_registry_delete_with_confirm():
    mock_svc = MagicMock()
    mock_svc.delete.return_value = {}
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "delete", "reg-001", "--confirm"],
        )
        assert result.exit_code == 0
        mock_svc.delete.assert_called_once_with("reg-001")


def test_cli_registry_delete_api_error():
    mock_svc = MagicMock()
    mock_svc.delete.side_effect = ApiError("boom", status_code=500)
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "delete", "reg-001", "--confirm"],
        )
        assert result.exit_code != 0
