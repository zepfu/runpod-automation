"""Integration tests for Phase 3: presets, --preset on create, profiles."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rpctl.main import app
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod

runner = CliRunner()


def _mock_settings():
    mock = MagicMock()
    mock.api_key = "test-key"
    return mock


def _preset_svc(tmp_path):
    from rpctl.services.preset_service import PresetService

    return PresetService(presets_dir=tmp_path / "presets")


# --- Preset CLI tests ---


def test_preset_help():
    result = runner.invoke(app, ["preset", "--help"])
    assert result.exit_code == 0
    assert "save" in result.output
    assert "list" in result.output
    assert "show" in result.output
    assert "delete" in result.output
    assert "apply" in result.output


def test_preset_save_and_list(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        result = runner.invoke(
            app,
            ["preset", "save", "my-pod", "--image", "nvidia/cuda", "--gpu-count", "2"],
        )
        assert result.exit_code == 0
        assert "saved" in result.output

        result = runner.invoke(app, ["preset", "list"])
        assert result.exit_code == 0
        assert "my-pod" in result.output


def test_preset_save_and_show(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        runner.invoke(
            app,
            ["preset", "save", "test-preset", "--image", "pytorch:2.1"],
        )
        result = runner.invoke(app, ["preset", "show", "test-preset"])
        assert result.exit_code == 0
        assert "test-preset" in result.output
        assert "pytorch:2.1" in result.output


def test_preset_save_and_delete(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        runner.invoke(
            app,
            ["preset", "save", "to-delete", "--image", "test"],
        )
        result = runner.invoke(app, ["preset", "delete", "to-delete", "--confirm"])
        assert result.exit_code == 0
        assert "deleted" in result.output


def test_preset_list_empty(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        result = runner.invoke(app, ["preset", "list"])
        assert result.exit_code == 0
        assert "No presets" in result.output


def test_preset_show_not_found(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        result = runner.invoke(app, ["preset", "show", "nonexistent"])
        assert result.exit_code != 0


def test_preset_save_json(tmp_path):
    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=_preset_svc(tmp_path),
    ):
        runner.invoke(
            app,
            ["preset", "save", "json-test", "--image", "test"],
        )
        result = runner.invoke(app, ["--json", "preset", "show", "json-test"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["metadata"]["name"] == "json-test"


# --- --from-pod tests ---


@pytest.fixture
def mock_pod_for_preset():
    return Pod(
        id="pod-capture",
        name="captured-pod",
        image_name="runpod/pytorch:2.1",
        gpu_type="NVIDIA RTX A6000",
        gpu_count=1,
        cloud_type="SECURE",
        container_disk_gb=100,
        volume_disk_gb=50,
        volume_mount_path="/workspace",
        ports="8888/http",
    )


def test_preset_save_from_pod(tmp_path, mock_pod_for_preset):
    mock_pod_svc = MagicMock()
    mock_pod_svc.get_pod.return_value = mock_pod_for_preset

    with (
        patch(
            "rpctl.cli.preset._get_preset_service",
            return_value=_preset_svc(tmp_path),
        ),
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.pod_service.PodService",
            return_value=mock_pod_svc,
        ),
    ):
        result = runner.invoke(
            app,
            ["preset", "save", "from-pod-test", "--from-pod", "pod-capture"],
        )
        assert result.exit_code == 0
        assert "saved" in result.output

        result = runner.invoke(app, ["--json", "preset", "show", "from-pod-test"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["params"]["image_name"] == "runpod/pytorch:2.1"
        assert parsed["metadata"]["resource_type"] == "pod"


# --- --from-endpoint tests ---


@pytest.fixture
def mock_endpoint_for_preset():
    return Endpoint(
        id="ep-capture",
        name="captured-ep",
        template_id="tmpl-456",
        gpu_ids="AMPERE_24",
        workers_min=0,
        workers_max=5,
        idle_timeout=10,
        flashboot=True,
    )


def test_preset_save_from_endpoint(tmp_path, mock_endpoint_for_preset):
    mock_ep_svc = MagicMock()
    mock_ep_svc.get_endpoint.return_value = mock_endpoint_for_preset

    with (
        patch(
            "rpctl.cli.preset._get_preset_service",
            return_value=_preset_svc(tmp_path),
        ),
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.endpoint_service.EndpointService",
            return_value=mock_ep_svc,
        ),
    ):
        result = runner.invoke(
            app,
            ["preset", "save", "from-ep-test", "--from-endpoint", "ep-capture"],
        )
        assert result.exit_code == 0
        assert "saved" in result.output


# --- --preset on pod create (patch get_config_dir so real PresetService works) ---


def test_pod_create_with_preset_dry_run(tmp_path):
    svc = _preset_svc(tmp_path)
    from rpctl.models.preset import Preset, PresetMetadata

    svc.save(
        Preset(
            metadata=PresetMetadata(name="gpu-pod", resource_type="pod", source="cli"),
            params={
                "image_name": "nvidia/cuda",
                "gpu_type_ids": ["NVIDIA RTX A6000"],
                "gpu_count": 1,
            },
        )
    )

    with patch(
        "rpctl.services.preset_service.get_config_dir",
        return_value=tmp_path,
    ):
        result = runner.invoke(
            app,
            ["pod", "create", "--preset", "gpu-pod", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "nvidia/cuda" in result.output


def test_pod_create_preset_with_override_dry_run(tmp_path):
    svc = _preset_svc(tmp_path)
    from rpctl.models.preset import Preset, PresetMetadata

    svc.save(
        Preset(
            metadata=PresetMetadata(name="base-pod", resource_type="pod", source="cli"),
            params={
                "image_name": "nvidia/cuda",
                "gpu_count": 1,
            },
        )
    )

    with patch(
        "rpctl.services.preset_service.get_config_dir",
        return_value=tmp_path,
    ):
        result = runner.invoke(
            app,
            ["pod", "create", "--preset", "base-pod", "--gpu-count", "4", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "4" in result.output


def test_pod_create_no_image_no_preset():
    result = runner.invoke(app, ["pod", "create", "--dry-run"])
    assert result.exit_code != 0
    assert "image" in result.output.lower()


# --- --preset on endpoint create ---


def test_endpoint_create_with_preset_dry_run(tmp_path):
    svc = _preset_svc(tmp_path)
    from rpctl.models.preset import Preset, PresetMetadata

    svc.save(
        Preset(
            metadata=PresetMetadata(name="my-ep", resource_type="endpoint", source="cli"),
            params={
                "name": "test-ep",
                "template_id": "tmpl-123",
                "gpu_ids": "AMPERE_24",
                "workers_max": 10,
            },
        )
    )

    with patch(
        "rpctl.services.preset_service.get_config_dir",
        return_value=tmp_path,
    ):
        result = runner.invoke(
            app,
            ["endpoint", "create", "--preset", "my-ep", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "tmpl-123" in result.output


# --- --save-preset on pod create ---


def test_pod_create_save_preset_dry_run(tmp_path):
    with patch(
        "rpctl.services.preset_service.get_config_dir",
        return_value=tmp_path,
    ):
        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "nvidia/cuda",
                "--save-preset",
                "saved-from-create",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "saved-from-create" in result.output
        assert "nvidia/cuda" in result.output


# --- Preset type mismatch ---


def test_preset_type_mismatch_pod(tmp_path):
    svc = _preset_svc(tmp_path)
    from rpctl.models.preset import Preset, PresetMetadata

    svc.save(
        Preset(
            metadata=PresetMetadata(name="ep-preset", resource_type="endpoint", source="cli"),
            params={"name": "ep", "template_id": "tmpl-1"},
        )
    )

    with patch(
        "rpctl.services.preset_service.get_config_dir",
        return_value=tmp_path,
    ):
        result = runner.invoke(
            app,
            ["pod", "create", "--preset", "ep-preset", "--dry-run"],
        )
        assert result.exit_code != 0
        assert "endpoint" in result.output.lower()


# --- Preset apply ---


def test_preset_apply_dry_run(tmp_path):
    svc = _preset_svc(tmp_path)
    from rpctl.models.preset import Preset, PresetMetadata

    svc.save(
        Preset(
            metadata=PresetMetadata(name="apply-test", resource_type="pod", source="cli"),
            params={"image_name": "test-image", "gpu_count": 2},
        )
    )

    with patch(
        "rpctl.cli.preset._get_preset_service",
        return_value=svc,
    ):
        result = runner.invoke(
            app,
            ["preset", "apply", "apply-test", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "test-image" in result.output


# --- Profile CLI tests ---


def test_config_add_profile(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["config", "add-profile", "staging"])
        assert result.exit_code == 0
        assert "staging" in result.output
        assert "added" in result.output


def test_config_use_profile(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings._data["profiles"]["staging"] = {"cloud_type": "community"}
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["config", "use-profile", "staging"])
        assert result.exit_code == 0
        assert "staging" in result.output


def test_config_add_duplicate_profile(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["config", "add-profile", "default"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_config_use_nonexistent_profile(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["config", "use-profile", "nonexistent"])
        assert result.exit_code != 0
