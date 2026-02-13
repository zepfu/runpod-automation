"""Integration tests for config CLI commands."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from rpctl.main import app

runner = CliRunner()


def test_config_help():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "set-key" in result.output
    assert "show" in result.output


def test_config_show_no_config():
    with patch("rpctl.cli.config.Settings.load", side_effect=Exception("not found")):
        result = runner.invoke(app, ["config", "show"])
        # Should handle gracefully
        assert result.exit_code != 0


def test_config_init(tmp_path):
    with (
        patch("rpctl.cli.config.get_config_dir", return_value=tmp_path / "rpctl"),
        patch("rpctl.cli.config.Settings.create_default"),
        patch("keyring.set_password") as mock_keyring,
    ):
        result = runner.invoke(
            app,
            ["config", "init"],
            input="test-api-key-123\ndefault\nsecure\n",
        )
        assert result.exit_code == 0
        assert "Configuration saved" in result.output
        mock_keyring.assert_called_once_with("rpctl", "default", "test-api-key-123")


def test_config_set(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "version: 1\n"
        "active_profile: default\n"
        "defaults:\n"
        "  cloud_type: secure\n"
        "profiles:\n"
        "  default:\n"
        "    cloud_type: secure\n"
    )

    from rpctl.config.settings import Settings

    real_settings = Settings.load(config_path=config_file)

    with patch("rpctl.cli.config.Settings.load", return_value=real_settings):
        result = runner.invoke(app, ["config", "set", "default_gpu", "NVIDIA RTX A6000"])
        assert result.exit_code == 0
        assert "default_gpu" in result.output


def test_config_get(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "version: 1\n"
        "active_profile: default\n"
        "defaults:\n"
        "  cloud_type: secure\n"
        "profiles:\n"
        "  default:\n"
        "    cloud_type: secure\n"
    )

    from rpctl.config.settings import Settings

    real_settings = Settings.load(config_path=config_file)

    with patch("rpctl.cli.config.Settings.load", return_value=real_settings):
        result = runner.invoke(app, ["config", "get", "cloud_type"])
        assert result.exit_code == 0
        assert "secure" in result.output


def test_config_get_missing_key(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "version: 1\nactive_profile: default\ndefaults: {}\nprofiles:\n  default: {}\n"
    )

    from rpctl.config.settings import Settings

    real_settings = Settings.load(config_path=config_file)

    with patch("rpctl.cli.config.Settings.load", return_value=real_settings):
        result = runner.invoke(app, ["config", "get", "nonexistent"])
        assert result.exit_code == 1
