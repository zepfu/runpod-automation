"""Tests for rpctl user commands and UserService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import RpctlError
from rpctl.main import app
from rpctl.services.user_service import UserService

runner = CliRunner()


# --- UserService unit tests ---


def test_user_service_get_info():
    """get_info() delegates to client.get_user()."""
    client = MagicMock()
    client.get_user.return_value = {"id": "user-123", "pubKey": "ssh-ed25519 AAAA"}
    svc = UserService(client)
    result = svc.get_info()
    assert result["id"] == "user-123"
    client.get_user.assert_called_once()


def test_user_service_set_ssh_key():
    """set_ssh_key() delegates to client.update_user_settings()."""
    client = MagicMock()
    client.update_user_settings.return_value = {"id": "user-123", "pubKey": "ssh-ed25519 AAAA"}
    svc = UserService(client)
    result = svc.set_ssh_key("ssh-ed25519 AAAA")
    assert result["pubKey"] == "ssh-ed25519 AAAA"
    client.update_user_settings.assert_called_once_with("ssh-ed25519 AAAA")


# --- CLI: rpctl user info ---


def test_cli_user_info():
    """rpctl user info returns account data."""
    mock_data = {"id": "user-123", "pubKey": "ssh-ed25519 AAAA", "networkVolumes": []}

    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_info.return_value = mock_data
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "info"])
        assert result.exit_code == 0
        mock_svc.get_info.assert_called_once()


def test_cli_user_info_json():
    """rpctl --output json user info outputs JSON."""
    mock_data = {"id": "user-123", "pubKey": "ssh-ed25519 AAAA", "networkVolumes": []}

    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_info.return_value = mock_data
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["--output", "json", "user", "info"])
        assert result.exit_code == 0
        assert "user-123" in result.output


def test_cli_user_info_api_error():
    """rpctl user info exits 1 on API error."""
    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_info.side_effect = RpctlError("API failure")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "info"])
        assert result.exit_code == 1


# --- CLI: rpctl user set-ssh-key ---


def test_cli_set_ssh_key_with_text():
    """rpctl user set-ssh-key --text passes key text to service."""
    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.set_ssh_key.return_value = {}
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "set-ssh-key", "--text", "ssh-ed25519 AAAAtest"])
        assert result.exit_code == 0
        mock_svc.set_ssh_key.assert_called_once_with("ssh-ed25519 AAAAtest")


def test_cli_set_ssh_key_with_file(tmp_path):
    """rpctl user set-ssh-key --key reads key from file."""
    key_file = tmp_path / "test.pub"
    key_file.write_text("ssh-ed25519 AAAAfromfile\n")

    with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.set_ssh_key.return_value = {}
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["user", "set-ssh-key", "--key", str(key_file)])
        assert result.exit_code == 0
        mock_svc.set_ssh_key.assert_called_once_with("ssh-ed25519 AAAAfromfile")


def test_cli_set_ssh_key_file_not_found():
    """rpctl user set-ssh-key --key exits 1 for missing file."""
    result = runner.invoke(app, ["user", "set-ssh-key", "--key", "/nonexistent/path/key.pub"])
    assert result.exit_code == 1


def test_cli_set_ssh_key_no_default():
    """rpctl user set-ssh-key exits 1 when no key found and no args given."""
    with patch("rpctl.cli.user.Path") as mock_path_cls:
        mock_instance = MagicMock()
        mock_instance.exists.return_value = False
        mock_path_cls.return_value.expanduser.return_value = mock_instance

        result = runner.invoke(app, ["user", "set-ssh-key"])
        assert result.exit_code == 1
