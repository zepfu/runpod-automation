"""Multi-profile management helpers."""

from __future__ import annotations

from rpctl.config.settings import Settings
from rpctl.errors import ConfigError


def add_profile(settings: Settings, name: str, cloud_type: str = "secure") -> None:
    """Add a new profile to the config."""
    profiles = settings._data.setdefault("profiles", {})
    if name in profiles:
        raise ConfigError(f"Profile '{name}' already exists.")
    profiles[name] = {"cloud_type": cloud_type}


def use_profile(settings: Settings, name: str) -> None:
    """Set the active profile."""
    profiles = settings._data.get("profiles", {})
    if name not in profiles:
        raise ConfigError(f"Profile '{name}' does not exist. Available: {list(profiles.keys())}")
    settings._data["active_profile"] = name
