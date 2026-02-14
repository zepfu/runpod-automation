"""Tests for remaining coverage gaps in rpctl.cli.registry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import RpctlError
from rpctl.main import app

runner = CliRunner()


def test_update_rpctl_error():
    """registry update exits with error code when service raises RpctlError."""
    mock_svc = MagicMock()
    mock_svc.update.side_effect = RpctlError("API failure")
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "update", "reg-001", "--username", "user"],
            input="password\n",
        )
        assert result.exit_code == 1


def test_delete_unconfirmed_prompt_yes():
    """registry delete without --confirm prompts and succeeds on 'y'."""
    mock_svc = MagicMock()
    mock_svc.delete.return_value = {}
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "delete", "reg-001"],
            input="y\n",
        )
        assert result.exit_code == 0
        mock_svc.delete.assert_called_once_with("reg-001")


def test_delete_unconfirmed_prompt_no():
    """registry delete without --confirm aborts on 'n'."""
    mock_svc = MagicMock()
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(
            app,
            ["registry", "delete", "reg-001"],
            input="n\n",
        )
        assert result.exit_code != 0
        mock_svc.delete.assert_not_called()


def test_list_rpctl_error():
    """registry list exits with error code when service raises RpctlError."""
    mock_svc = MagicMock()
    mock_svc.list.side_effect = RpctlError("Network error")
    with patch("rpctl.cli.registry._get_registry_service", return_value=mock_svc):
        result = runner.invoke(app, ["registry", "list"])
        assert result.exit_code == 1
