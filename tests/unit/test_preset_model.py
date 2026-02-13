"""Unit tests for preset models and merge logic."""

from __future__ import annotations

from rpctl.models.preset import Preset, PresetMetadata
from rpctl.services.preset_service import PresetService


class TestPresetModel:
    def test_roundtrip_pod(self):
        preset = Preset(
            metadata=PresetMetadata(name="test", resource_type="pod", source="cli"),
            params={"image_name": "nvidia/cuda", "gpu_count": 2},
        )
        data = preset.model_dump()
        restored = Preset(**data)
        assert restored.metadata.name == "test"
        assert restored.params["image_name"] == "nvidia/cuda"

    def test_roundtrip_endpoint(self):
        preset = Preset(
            metadata=PresetMetadata(name="ep-test", resource_type="endpoint"),
            params={"template_id": "tmpl-123", "workers_max": 10},
        )
        data = preset.model_dump()
        restored = Preset(**data)
        assert restored.metadata.resource_type == "endpoint"
        assert restored.params["workers_max"] == 10

    def test_metadata_defaults(self):
        meta = PresetMetadata(name="x", resource_type="pod")
        assert meta.created_at  # auto-set
        assert meta.description == ""
        assert meta.source == ""


class TestPresetMerge:
    def test_cli_overrides_win(self):
        result = PresetService.merge_preset_with_overrides(
            {"gpu_count": 1, "image_name": "old"},
            {"gpu_count": 4},
        )
        assert result["gpu_count"] == 4
        assert result["image_name"] == "old"

    def test_none_overrides_skipped(self):
        result = PresetService.merge_preset_with_overrides(
            {"gpu_count": 2},
            {"gpu_count": None, "image_name": None},
        )
        assert result["gpu_count"] == 2
        assert "image_name" not in result

    def test_env_merge_is_additive(self):
        result = PresetService.merge_preset_with_overrides(
            {"env": {"A": "1", "B": "2"}},
            {"env": {"B": "override", "C": "3"}},
        )
        assert result["env"] == {"A": "1", "B": "override", "C": "3"}

    def test_empty_list_not_applied(self):
        result = PresetService.merge_preset_with_overrides(
            {"gpu_type_ids": ["RTX A6000"]},
            {"gpu_type_ids": []},
        )
        assert result["gpu_type_ids"] == ["RTX A6000"]

    def test_nonempty_list_overrides(self):
        result = PresetService.merge_preset_with_overrides(
            {"gpu_type_ids": ["RTX A6000"]},
            {"gpu_type_ids": ["RTX 4090"]},
        )
        assert result["gpu_type_ids"] == ["RTX 4090"]

    def test_preset_only_no_overrides(self):
        result = PresetService.merge_preset_with_overrides(
            {"gpu_count": 2, "image_name": "test"},
            {},
        )
        assert result == {"gpu_count": 2, "image_name": "test"}

    def test_overrides_only_no_preset(self):
        result = PresetService.merge_preset_with_overrides(
            {},
            {"gpu_count": 4},
        )
        assert result == {"gpu_count": 4}
