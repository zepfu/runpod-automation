"""Configuration loading and resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from rpctl.config.constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    DEFAULT_CLOUD_TYPE,
    KEYRING_SERVICE,
)
from rpctl.errors import AuthenticationError, ConfigError


def get_config_dir() -> Path:
    """Return the rpctl config directory path."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / CONFIG_DIR_NAME
    return Path.home() / ".config" / CONFIG_DIR_NAME


def get_config_path() -> Path:
    """Return the path to the config YAML file."""
    return get_config_dir() / CONFIG_FILE_NAME


class Settings:
    """Manages rpctl configuration with env var > keyring > YAML > defaults resolution."""

    def __init__(self, data: dict[str, Any], config_path: Path | None = None):
        self._data = data
        self._config_path = config_path or get_config_path()

    @classmethod
    def load(cls, profile: str | None = None, config_path: Path | None = None) -> Settings:
        """Load settings from the config file."""
        path = config_path or get_config_path()
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}. Run 'rpctl config init'.")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        settings = cls(data, config_path=path)
        if profile:
            settings._data["active_profile"] = profile
        return settings

    @classmethod
    def create_default(
        cls,
        active_profile: str = "default",
        cloud_type: str = DEFAULT_CLOUD_TYPE,
    ) -> Settings:
        """Create a new Settings with default values."""
        data = {
            "version": 1,
            "active_profile": active_profile,
            "defaults": {
                "cloud_type": cloud_type,
                "output_format": "table",
            },
            "profiles": {
                active_profile: {
                    "cloud_type": cloud_type,
                },
            },
        }
        return cls(data)

    def save(self) -> None:
        """Write the config to disk."""
        path = self._config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)

    @property
    def active_profile(self) -> str:
        return str(self._data.get("active_profile", "default"))

    @property
    def api_key(self) -> str:
        """Resolve API key: env var > keyring."""
        key = os.environ.get("RUNPOD_API_KEY")
        if key:
            return key

        import keyring

        key = keyring.get_password(KEYRING_SERVICE, self.active_profile)
        if key:
            return key

        raise AuthenticationError(
            f"No API key found for profile '{self.active_profile}'. "
            "Run 'rpctl config set-key' or set RUNPOD_API_KEY."
        )

    def has_api_key(self) -> bool:
        """Check if an API key is available without raising."""
        try:
            _ = self.api_key
            return True
        except AuthenticationError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Resolve a config value: profile > defaults > provided default."""
        profiles = self._data.get("profiles", {})
        profile_data = profiles.get(self.active_profile, {})
        if key in profile_data:
            return profile_data[key]

        defaults = self._data.get("defaults", {})
        if key in defaults:
            return defaults[key]

        return default

    def set_default(self, key: str, value: str) -> None:
        """Set a value in the active profile."""
        profiles = self._data.setdefault("profiles", {})
        profile = profiles.setdefault(self.active_profile, {})
        profile[key] = value

    def list_profiles(self) -> list[str]:
        """Return all profile names."""
        return list(self._data.get("profiles", {}).keys())

    def to_display_dict(self) -> dict[str, Any]:
        """Return a dict suitable for display (no secrets)."""
        return {
            "active_profile": self.active_profile,
            "cloud_type": self.get("cloud_type", DEFAULT_CLOUD_TYPE),
            "output_format": self.get("output_format", "table"),
            "config_path": str(self._config_path),
        }
