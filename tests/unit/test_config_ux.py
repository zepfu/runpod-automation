"""Unit tests for config UX improvements — key masking and keyring error handling."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from rpctl.errors import AuthenticationError


class _NoKeyringError(Exception):
    """Simulated NoKeyringError from keyring package."""

    pass


# Name it exactly as the real error class for type-name matching
_NoKeyringError.__name__ = "NoKeyringError"


class TestStoreKeyring:
    """Tests for _store_keyring helper in config.py."""

    def test_store_keyring_success(self):
        """_store_keyring calls keyring.set_password."""
        mock_keyring = MagicMock()
        with patch.dict(sys.modules, {"keyring": mock_keyring}):
            from rpctl.cli.config import _store_keyring

            _store_keyring("default", "test-key")
            mock_keyring.set_password.assert_called_once_with(
                "rpctl", "default", "test-key"
            )

    def test_store_keyring_no_backend(self):
        """NoKeyringError triggers helpful message and exit."""
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = _NoKeyringError("no backend")
        with (
            patch.dict(sys.modules, {"keyring": mock_keyring}),
            pytest.raises(typer.Exit) as exc_info,
        ):
            from rpctl.cli.config import _store_keyring

            _store_keyring("default", "test-key")
        assert exc_info.value.exit_code == 1

    def test_store_keyring_no_backend_by_message(self):
        """Catches errors with 'no backend' in message string."""
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = RuntimeError(
            "no backend available"
        )
        with (
            patch.dict(sys.modules, {"keyring": mock_keyring}),
            pytest.raises(typer.Exit) as exc_info,
        ):
            from rpctl.cli.config import _store_keyring

            _store_keyring("default", "test-key")
        assert exc_info.value.exit_code == 1

    def test_store_keyring_other_error_reraises(self):
        """Non-keyring errors propagate."""
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = RuntimeError("disk full")
        with (
            patch.dict(sys.modules, {"keyring": mock_keyring}),
            pytest.raises(RuntimeError, match="disk full"),
        ):
            from rpctl.cli.config import _store_keyring

            _store_keyring("default", "test-key")


class TestSettingsApiKeyKeyring:
    """Tests for Settings.api_key keyring error handling."""

    def test_env_var_precedence(self):
        """RUNPOD_API_KEY env var takes precedence over keyring."""
        from rpctl.config.settings import Settings

        s = Settings({"active_profile": "default"})
        with patch.dict("os.environ", {"RUNPOD_API_KEY": "env-key"}):
            assert s.api_key == "env-key"

    def test_keyring_fallback(self):
        """Falls back to keyring when env var not set."""
        import os

        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "keyring-key"
        from rpctl.config.settings import Settings

        s = Settings({"active_profile": "default"})
        env_backup = os.environ.pop("RUNPOD_API_KEY", None)
        try:
            with patch.dict(sys.modules, {"keyring": mock_keyring}):
                assert s.api_key == "keyring-key"
        finally:
            if env_backup is not None:
                os.environ["RUNPOD_API_KEY"] = env_backup

    def test_no_keyring_backend_raises_auth_error(self):
        """NoKeyringError raises AuthenticationError with install suggestion."""
        import os

        mock_keyring = MagicMock()
        mock_keyring.get_password.side_effect = _NoKeyringError("no backend")
        from rpctl.config.settings import Settings

        s = Settings({"active_profile": "default"})
        env_backup = os.environ.pop("RUNPOD_API_KEY", None)
        try:
            with (
                patch.dict(sys.modules, {"keyring": mock_keyring}),
                pytest.raises(AuthenticationError, match="keyrings.alt"),
            ):
                s.api_key
        finally:
            if env_backup is not None:
                os.environ["RUNPOD_API_KEY"] = env_backup

    def test_no_key_found_raises_auth_error(self):
        """Missing key raises AuthenticationError with instructions."""
        import os

        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None
        from rpctl.config.settings import Settings

        s = Settings({"active_profile": "default"})
        env_backup = os.environ.pop("RUNPOD_API_KEY", None)
        try:
            with (
                patch.dict(sys.modules, {"keyring": mock_keyring}),
                pytest.raises(AuthenticationError, match="set-key"),
            ):
                s.api_key
        finally:
            if env_backup is not None:
                os.environ["RUNPOD_API_KEY"] = env_backup


class TestConfigInitRichPrompt:
    """Tests for Rich Prompt usage in config commands."""

    def test_config_init_uses_rich_prompt(self):
        """init() calls Prompt.ask with password=True for API key."""
        from typer.testing import CliRunner

        from rpctl.main import app

        runner = CliRunner()
        with (
            patch("rpctl.cli.config.Prompt") as mock_prompt_cls,
            patch("rpctl.cli.config._store_keyring") as mock_store,
            patch("rpctl.cli.config.get_config_dir") as mock_dir,
            patch("rpctl.cli.config.Settings") as mock_settings_cls,
        ):
            mock_prompt_cls.ask.return_value = "test-api-key"
            mock_dir.return_value = MagicMock(spec=Path)
            mock_settings = MagicMock()
            mock_settings_cls.create_default.return_value = mock_settings

            result = runner.invoke(
                app, ["config", "init"], input="default\nsecure\n"
            )
            mock_prompt_cls.ask.assert_called_once_with(
                "RunPod API key", password=True
            )

    def test_config_set_key_uses_rich_prompt(self):
        """set_key() calls Prompt.ask with password=True for API key."""
        from typer.testing import CliRunner

        from rpctl.main import app

        runner = CliRunner()
        with (
            patch("rpctl.cli.config.Prompt") as mock_prompt_cls,
            patch("rpctl.cli.config._store_keyring") as mock_store,
            patch("rpctl.cli.config.Settings") as mock_settings_cls,
        ):
            mock_settings = MagicMock()
            mock_settings.active_profile = "default"
            mock_settings_cls.load.return_value = mock_settings
            mock_prompt_cls.ask.return_value = "new-api-key"

            result = runner.invoke(app, ["config", "set-key"])
            mock_prompt_cls.ask.assert_called_once_with(
                "API key for profile 'default'", password=True
            )
