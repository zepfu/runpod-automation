"""Unit tests for config system."""

from __future__ import annotations

import pytest

from rpctl.config.profiles import add_profile, use_profile
from rpctl.config.settings import Settings
from rpctl.errors import AuthenticationError, ConfigError


class TestSettings:
    def test_load_from_file(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        assert settings.active_profile == "default"

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(ConfigError, match="Config file not found"):
            Settings.load(config_path=tmp_path / "nonexistent.yaml")

    def test_profile_override(self, tmp_config):
        settings = Settings.load(profile="work", config_path=tmp_config)
        assert settings.active_profile == "work"

    def test_get_profile_value(self, tmp_config):
        settings = Settings.load(profile="work", config_path=tmp_config)
        assert settings.get("cloud_type") == "community"

    def test_get_falls_back_to_defaults(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        assert settings.get("output_format") == "table"

    def test_get_returns_default_when_missing(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        assert settings.get("nonexistent", "fallback") == "fallback"

    def test_set_default(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        settings.set_default("default_gpu", "NVIDIA RTX A6000")
        assert settings.get("default_gpu") == "NVIDIA RTX A6000"

    def test_save_roundtrip(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        settings.set_default("test_key", "test_value")
        settings.save()

        reloaded = Settings.load(config_path=tmp_config)
        assert reloaded.get("test_key") == "test_value"

    def test_create_default(self):
        settings = Settings.create_default(
            active_profile="test",
            cloud_type="community",
        )
        assert settings.active_profile == "test"
        assert settings.get("cloud_type") == "community"

    def test_list_profiles(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        profiles = settings.list_profiles()
        assert "default" in profiles
        assert "work" in profiles

    def test_to_display_dict(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        display = settings.to_display_dict()
        assert "active_profile" in display
        assert "cloud_type" in display
        assert "api_key" not in display

    def test_api_key_from_env(self, tmp_config, monkeypatch):
        monkeypatch.setenv("RUNPOD_API_KEY", "test-key-123")
        settings = Settings.load(config_path=tmp_config)
        assert settings.api_key == "test-key-123"

    def test_api_key_missing_raises(self, tmp_config, monkeypatch):
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        # Mock keyring to return None
        from unittest.mock import patch

        import keyring

        with patch.object(keyring, "get_password", return_value=None):
            settings = Settings.load(config_path=tmp_config)
            with pytest.raises(AuthenticationError, match="No API key found"):
                _ = settings.api_key

    def test_has_api_key_true(self, tmp_config, monkeypatch):
        monkeypatch.setenv("RUNPOD_API_KEY", "test-key")
        settings = Settings.load(config_path=tmp_config)
        assert settings.has_api_key() is True

    def test_has_api_key_false(self, tmp_config, monkeypatch):
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        from unittest.mock import patch

        import keyring

        with patch.object(keyring, "get_password", return_value=None):
            settings = Settings.load(config_path=tmp_config)
            assert settings.has_api_key() is False


class TestProfiles:
    def test_add_profile(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        add_profile(settings, "staging", cloud_type="community")
        assert "staging" in settings.list_profiles()

    def test_add_duplicate_raises(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        with pytest.raises(ConfigError, match="already exists"):
            add_profile(settings, "default")

    def test_use_profile(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        use_profile(settings, "work")
        assert settings.active_profile == "work"

    def test_use_nonexistent_raises(self, tmp_config):
        settings = Settings.load(config_path=tmp_config)
        with pytest.raises(ConfigError, match="does not exist"):
            use_profile(settings, "nonexistent")
