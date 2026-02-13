"""Preset management — file-based CRUD for saved configurations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from rpctl.config.constants import PRESETS_DIR_NAME
from rpctl.config.settings import get_config_dir
from rpctl.errors import PresetError
from rpctl.models.preset import Preset

_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def _validate_name(name: str) -> None:
    """Ensure preset name is safe for filesystem use."""
    if not name or not _NAME_RE.match(name):
        msg = (
            f"Invalid preset name '{name}'. "
            "Use alphanumeric characters, hyphens, and underscores only."
        )
        raise PresetError(msg)


class PresetService:
    """Manage local preset YAML files."""

    def __init__(self, presets_dir: Path | None = None) -> None:
        self._dir = presets_dir or (get_config_dir() / PRESETS_DIR_NAME)

    def _path_for(self, name: str) -> Path:
        return self._dir / f"{name}.yaml"

    def exists(self, name: str) -> bool:
        """Check if a preset with the given name exists."""
        return self._path_for(name).is_file()

    def save(self, preset: Preset, *, overwrite: bool = False) -> Path:
        """Write a preset to a YAML file. Returns the file path."""
        _validate_name(preset.metadata.name)
        path = self._path_for(preset.metadata.name)

        if path.exists() and not overwrite:
            msg = f"Preset '{preset.metadata.name}' already exists. Use --overwrite to replace it."
            raise PresetError(msg)

        self._dir.mkdir(parents=True, exist_ok=True)
        data = preset.model_dump(exclude_none=True)
        path.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))
        return path

    def load(self, name: str) -> Preset:
        """Load a preset by name."""
        _validate_name(name)
        path = self._path_for(name)
        if not path.is_file():
            raise PresetError(f"Preset '{name}' not found.")

        raw = yaml.safe_load(path.read_text())
        return Preset(**raw)

    def list_presets(self) -> list[Preset]:
        """Return all presets, sorted by name."""
        if not self._dir.is_dir():
            return []

        presets: list[Preset] = []
        for path in sorted(self._dir.glob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text())
                presets.append(Preset(**raw))
            except Exception:  # noqa: BLE001
                continue  # skip malformed files
        return presets

    def delete(self, name: str) -> None:
        """Delete a preset file."""
        _validate_name(name)
        path = self._path_for(name)
        if not path.is_file():
            raise PresetError(f"Preset '{name}' not found.")
        path.unlink()

    # --- Extraction helpers ---

    @staticmethod
    def params_from_pod(pod: Any) -> dict[str, Any]:
        """Extract preset params from a live Pod object."""
        env_dict: dict[str, str] = {}
        if pod.env:
            for entry in pod.env:
                key = entry.get("key", "")
                value = entry.get("value", "")
                if key:
                    env_dict[key] = value

        params: dict[str, Any] = {
            "name": pod.name,
            "image_name": pod.image_name,
            "gpu_count": pod.gpu_count,
            "cloud_type": pod.cloud_type,
            "container_disk_in_gb": pod.container_disk_gb,
            "volume_in_gb": pod.volume_disk_gb,
            "volume_mount_path": pod.volume_mount_path,
            "ports": pod.ports,
        }
        if pod.gpu_type:
            params["gpu_type_ids"] = [pod.gpu_type]
        if env_dict:
            params["env"] = env_dict
        return params

    @staticmethod
    def params_from_endpoint(endpoint: Any) -> dict[str, Any]:
        """Extract preset params from a live Endpoint object."""
        return {
            "name": endpoint.name,
            "template_id": endpoint.template_id,
            "gpu_ids": endpoint.gpu_ids,
            "gpu_count": endpoint.gpu_count,
            "workers_min": endpoint.workers_min,
            "workers_max": endpoint.workers_max,
            "idle_timeout": endpoint.idle_timeout,
            "scaler_type": endpoint.scaler_type,
            "scaler_value": endpoint.scaler_value,
            "network_volume_id": endpoint.network_volume_id,
            "flashboot": endpoint.flashboot,
            "locations": endpoint.locations,
        }

    # --- Merge helper ---

    @staticmethod
    def merge_preset_with_overrides(
        preset_params: dict[str, Any],
        cli_overrides: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge preset values with explicit CLI overrides.

        CLI overrides win. None values are skipped.
        Dict fields (env) merge additively.
        Empty list means "not provided" and is skipped.
        """
        merged = dict(preset_params)
        for key, value in cli_overrides.items():
            if value is None:
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return merged
