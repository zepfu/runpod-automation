"""Tests for remaining coverage gaps in rpctl.cli.user."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import RpctlError
from rpctl.main import app

runner = CliRunner()


def test_set_ssh_key_default_key_found():
    """set-ssh-key with no args finds a default key and uses it."""
    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.set_ssh_key.return_value = {}
        mock_svc_fn.return_value = mock_svc

        with patch("rpctl.cli.user.Path") as mock_path_cls:
            mock_instance = MagicMock()
            # First default key path exists
            mock_instance.exists.return_value = True
            mock_instance.read_text.return_value = "ssh-ed25519 AAAAdefault\n"
            mock_instance.__str__ = lambda self: "/home/user/.ssh/id_ed25519.pub"
            mock_path_cls.return_value.expanduser.return_value = mock_instance

            result = runner.invoke(app, ["user", "set-ssh-key"])
            assert result.exit_code == 0
            mock_svc.set_ssh_key.assert_called_once_with("ssh-ed25519 AAAAdefault")
            assert "Using key:" in result.output


def test_set_ssh_key_rpctl_error():
    """set-ssh-key exits with error code when service raises RpctlError."""
    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.set_ssh_key.side_effect = RpctlError("API failure")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "set-ssh-key", "--text", "ssh-ed25519 AAAAtest"])
        assert result.exit_code == 1


def test_info_rpctl_error():
    """info command exits with error code when service raises RpctlError."""
    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_info.side_effect = RpctlError("API failure")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "info"])
        assert result.exit_code == 1
