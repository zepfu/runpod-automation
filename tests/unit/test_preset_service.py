"""Unit tests for PresetService."""

from __future__ import annotations

import pytest
from rpctl.errors import PresetError
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod
from rpctl.models.preset import Preset, PresetMetadata
from rpctl.services.preset_service import PresetService


def _make_preset(name: str = "test", resource_type: str = "pod", **params) -> Preset:
    return Preset(
        metadata=PresetMetadata(name=name, resource_type=resource_type, source="cli"),
        params=params or {"image_name": "nvidia/cuda"},
    )


class TestPresetCRUD:
    def test_save_creates_directory(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path / "presets")
        preset = _make_preset()
        path = svc.save(preset)
        assert path.exists()
        assert (tmp_path / "presets").is_dir()

    def test_save_writes_valid_yaml(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset())
        loaded = svc.load("test")
        assert loaded.metadata.name == "test"
        assert loaded.params["image_name"] == "nvidia/cuda"

    def test_save_overwrite_blocked(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset())
        with pytest.raises(PresetError, match="already exists"):
            svc.save(_make_preset())

    def test_save_overwrite_allowed(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset())
        svc.save(_make_preset(image_name="updated"), overwrite=True)
        loaded = svc.load("test")
        assert loaded.params["image_name"] == "updated"

    def test_load_nonexistent_raises(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        with pytest.raises(PresetError, match="not found"):
            svc.load("nonexistent")

    def test_list_empty(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        assert svc.list_presets() == []

    def test_list_multiple(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset("alpha"))
        svc.save(_make_preset("beta"))
        presets = svc.list_presets()
        assert len(presets) == 2
        assert presets[0].metadata.name == "alpha"
        assert presets[1].metadata.name == "beta"

    def test_delete_removes_file(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset())
        svc.delete("test")
        assert not svc.exists("test")

    def test_delete_nonexistent_raises(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        with pytest.raises(PresetError, match="not found"):
            svc.delete("nonexistent")

    def test_exists_true(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        svc.save(_make_preset())
        assert svc.exists("test") is True

    def test_exists_false(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        assert svc.exists("nope") is False


class TestNameValidation:
    def test_valid_names(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        for name in ["my-pod", "test_1", "A123", "gpu-dev-env"]:
            svc.save(_make_preset(name))
            assert svc.exists(name)

    def test_rejects_path_traversal(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        with pytest.raises(PresetError, match="Invalid preset name"):
            svc.save(_make_preset("../etc/passwd"))

    def test_rejects_special_chars(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        with pytest.raises(PresetError, match="Invalid preset name"):
            svc.save(_make_preset("my preset!"))

    def test_rejects_empty(self, tmp_path):
        svc = PresetService(presets_dir=tmp_path)
        with pytest.raises(PresetError, match="Invalid preset name"):
            svc.save(_make_preset(""))


class TestParamsExtraction:
    def test_from_pod(self):
        pod = Pod(
            id="pod-123",
            name="my-pod",
            image_name="runpod/pytorch:2.1",
            gpu_type="NVIDIA RTX A6000",
            gpu_count=1,
            cloud_type="SECURE",
            container_disk_gb=50,
            volume_disk_gb=20,
            volume_mount_path="/workspace",
            ports="8888/http",
        )
        params = PresetService.params_from_pod(pod)
        assert params["name"] == "my-pod"
        assert params["image_name"] == "runpod/pytorch:2.1"
        assert params["gpu_type_ids"] == ["NVIDIA RTX A6000"]

    def test_from_pod_with_env(self):
        pod = Pod(
            id="pod-123",
            env=[{"key": "TOKEN", "value": "abc"}, {"key": "MODE", "value": "dev"}],
        )
        params = PresetService.params_from_pod(pod)
        assert params["env"] == {"TOKEN": "abc", "MODE": "dev"}

    def test_from_pod_minimal(self):
        pod = Pod(id="pod-min")
        params = PresetService.params_from_pod(pod)
        assert params["name"] == ""
        assert "gpu_type_ids" not in params  # empty gpu_type is skipped

    def test_from_endpoint(self):
        ep = Endpoint(
            id="ep-123",
            name="my-ep",
            template_id="tmpl-123",
            gpu_ids="AMPERE_24",
            workers_min=0,
            workers_max=5,
            idle_timeout=10,
            flashboot=True,
        )
        params = PresetService.params_from_endpoint(ep)
        assert params["name"] == "my-ep"
        assert params["template_id"] == "tmpl-123"
        assert params["flashboot"] is True
        assert params["workers_max"] == 5
