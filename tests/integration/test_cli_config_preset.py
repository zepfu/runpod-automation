"""Integration tests for config and preset CLI commands — coverage gaps."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import ApiError, ConfigError, PresetError
from rpctl.main import app
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod

runner = CliRunner()


def _mock_settings():
    mock = MagicMock()
    mock.api_key = "test-key"
    mock.active_profile = "default"
    mock.has_api_key.return_value = True
    mock.to_display_dict.return_value = {
        "active_profile": "default",
        "cloud_type": "secure",
        "output_format": "table",
        "config_path": "/tmp/rpctl/config.yaml",
    }
    mock.list_profiles.return_value = ["default", "staging"]
    mock.get.return_value = "some-value"
    return mock


# =============================================================================
# Config CLI
# =============================================================================


def test_config_init():
    """config init stores key and saves settings."""
    import sys

    mock_keyring = MagicMock()
    with (
        patch("rpctl.cli.config.get_config_dir", return_value=Path("/tmp/rpctl-test")),
        patch("rpctl.cli.config.typer.prompt", side_effect=["test-api-key", "default", "secure"]),
        patch.dict(sys.modules, {"keyring": mock_keyring}),
        patch("rpctl.cli.config.Settings.create_default") as mock_create,
    ):
        mock_s = MagicMock()
        mock_create.return_value = mock_s
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0
        assert "Configuration saved" in result.output


def test_config_init_empty_key():
    """config init rejects empty API key."""
    with (
        patch("rpctl.cli.config.get_config_dir", return_value=Path("/tmp/rpctl-test")),
        patch("rpctl.cli.config.typer.prompt", side_effect=["   ", "default", "secure"]),
    ):
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 1


def test_config_set_key():
    """config set-key stores key in keyring."""
    import sys

    mock_keyring = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.cli.config.typer.prompt", return_value="new-api-key"),
        patch.dict(sys.modules, {"keyring": mock_keyring}),
    ):
        result = runner.invoke(app, ["config", "set-key"])
        assert result.exit_code == 0
        assert "API key stored" in result.output


def test_config_set_key_empty():
    """config set-key rejects empty key."""
    import sys

    mock_keyring = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.cli.config.typer.prompt", return_value="   "),
        patch.dict(sys.modules, {"keyring": mock_keyring}),
    ):
        result = runner.invoke(app, ["config", "set-key"])
        assert result.exit_code == 1


def test_config_show_no_config():
    """config show handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 3


def test_config_list_profiles_no_config():
    """config list-profiles handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "list-profiles"])
        assert result.exit_code == 3


def test_config_add_profile():
    """config add-profile adds a profile."""
    mock_s = _mock_settings()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=mock_s),
        patch("rpctl.config.profiles.add_profile"),
    ):
        result = runner.invoke(app, ["config", "add-profile", "staging"])
        assert result.exit_code == 0
        assert "staging" in result.output


def test_config_add_profile_no_config():
    """config add-profile handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "add-profile", "staging"])
        assert result.exit_code == 3


def test_config_add_profile_error():
    """config add-profile handles duplicate profile."""
    mock_s = _mock_settings()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=mock_s),
        patch("rpctl.config.profiles.add_profile", side_effect=ConfigError("already exists")),
    ):
        result = runner.invoke(app, ["config", "add-profile", "default"])
        assert result.exit_code == 1


def test_config_use_profile():
    """config use-profile switches active profile."""
    mock_s = _mock_settings()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=mock_s),
        patch("rpctl.config.profiles.use_profile"),
    ):
        result = runner.invoke(app, ["config", "use-profile", "staging"])
        assert result.exit_code == 0
        assert "staging" in result.output


def test_config_use_profile_no_config():
    """config use-profile handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "use-profile", "staging"])
        assert result.exit_code == 3


def test_config_use_profile_error():
    """config use-profile handles nonexistent profile."""
    mock_s = _mock_settings()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=mock_s),
        patch("rpctl.config.profiles.use_profile", side_effect=ConfigError("not found")),
    ):
        result = runner.invoke(app, ["config", "use-profile", "nonexistent"])
        assert result.exit_code == 1


def test_config_set():
    """config set stores a value."""
    mock_s = _mock_settings()
    with patch("rpctl.config.settings.Settings.load", return_value=mock_s):
        result = runner.invoke(app, ["config", "set", "cloud_type", "community"])
        assert result.exit_code == 0
        assert "cloud_type" in result.output


def test_config_set_no_config():
    """config set handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "set", "cloud_type", "community"])
        assert result.exit_code == 3


def test_config_get():
    """config get reads a value."""
    mock_s = _mock_settings()
    with patch("rpctl.config.settings.Settings.load", return_value=mock_s):
        result = runner.invoke(app, ["config", "get", "cloud_type"])
        assert result.exit_code == 0


def test_config_get_no_config():
    """config get handles missing config."""
    with patch("rpctl.config.settings.Settings.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["config", "get", "cloud_type"])
        assert result.exit_code == 3


def test_config_get_missing_key():
    """config get handles unset key."""
    mock_s = _mock_settings()
    mock_s.get.return_value = None
    with patch("rpctl.config.settings.Settings.load", return_value=mock_s):
        result = runner.invoke(app, ["config", "get", "nonexistent"])
        assert result.exit_code == 1


# =============================================================================
# Preset CLI — save command
# =============================================================================


@contextmanager
def _preset_svc_ctx(mock_svc):
    with patch("rpctl.cli.preset._get_preset_service", return_value=mock_svc):
        yield


def _mock_pod():
    return Pod(
        id="pod-001",
        name="test-pod",
        status="RUNNING",
        gpu_type="A6000",
        gpu_count=1,
        image_name="nvidia/cuda",
        cloud_type="SECURE",
    )


def _mock_endpoint():
    return Endpoint(
        id="ep-001",
        name="test-ep",
        template_id="tmpl-1",
        gpu_ids="AMPERE_24",
        workers_min=0,
        workers_max=5,
    )


def test_preset_save_from_pod():
    """preset save --from-pod captures pod config."""
    mock_svc = MagicMock()
    mock_svc.save.return_value = Path("/tmp/preset.yaml")
    mock_pod_svc = MagicMock()
    mock_pod_svc.get_pod.return_value = _mock_pod()
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_pod_service", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["preset", "save", "my-preset", "--from-pod", "pod-001"])
        assert result.exit_code == 0
        assert "my-preset" in result.output


def test_preset_save_from_endpoint():
    """preset save --from-endpoint captures endpoint config."""
    mock_svc = MagicMock()
    mock_svc.save.return_value = Path("/tmp/preset.yaml")
    mock_ep_svc = MagicMock()
    mock_ep_svc.get_endpoint.return_value = _mock_endpoint()
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_endpoint_service", return_value=mock_ep_svc),
    ):
        result = runner.invoke(
            app, ["preset", "save", "my-preset", "--from-endpoint", "ep-001", "--type", "endpoint"]
        )
        assert result.exit_code == 0


def test_preset_save_both_from_flags():
    """preset save rejects --from-pod and --from-endpoint together."""
    mock_svc = MagicMock()
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(
            app, ["preset", "save", "test", "--from-pod", "p1", "--from-endpoint", "e1"]
        )
        assert result.exit_code == 1


def test_preset_save_from_pod_error():
    """preset save --from-pod handles API error."""
    mock_svc = MagicMock()
    mock_pod_svc = MagicMock()
    mock_pod_svc.get_pod.side_effect = ApiError("not found", status_code=404)
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_pod_service", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["preset", "save", "test", "--from-pod", "bad-id"])
        assert result.exit_code != 0


def test_preset_save_from_endpoint_error():
    """preset save --from-endpoint handles API error."""
    mock_svc = MagicMock()
    mock_ep_svc = MagicMock()
    mock_ep_svc.get_endpoint.side_effect = ApiError("not found", status_code=404)
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_endpoint_service", return_value=mock_ep_svc),
    ):
        result = runner.invoke(
            app, ["preset", "save", "test", "--from-endpoint", "bad-id", "--type", "endpoint"]
        )
        assert result.exit_code != 0


def test_preset_save_with_cli_overrides():
    """preset save builds params from CLI flags."""
    mock_svc = MagicMock()
    mock_svc.save.return_value = Path("/tmp/preset.yaml")
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(
            app,
            [
                "preset",
                "save",
                "test",
                "--image",
                "nvidia/cuda",
                "--gpu",
                "A100",
                "--gpu-count",
                "2",
                "--cloud-type",
                "secure",
                "--workers-min",
                "0",
                "--workers-max",
                "5",
                "--template",
                "tmpl-1",
            ],
        )
        assert result.exit_code == 0


def test_preset_save_no_params():
    """preset save with no params shows error."""
    mock_svc = MagicMock()
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "save", "test"])
        assert result.exit_code == 1


def test_preset_save_invalid_type():
    """preset save with invalid resource type shows error."""
    mock_svc = MagicMock()
    mock_svc.save.return_value = Path("/tmp/preset.yaml")
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(
            app, ["preset", "save", "test", "--type", "invalid", "--image", "img"]
        )
        assert result.exit_code == 1


def test_preset_save_preset_error():
    """preset save handles save error (already exists)."""
    mock_svc = MagicMock()
    mock_svc.save.side_effect = PresetError("already exists")
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "save", "test", "--image", "img"])
        assert result.exit_code != 0


# =============================================================================
# Preset CLI — delete command
# =============================================================================


def test_preset_delete_confirmed():
    """preset delete with --confirm deletes."""
    mock_svc = MagicMock()
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "delete", "test", "--confirm"])
        assert result.exit_code == 0
        mock_svc.delete.assert_called_once_with("test")


def test_preset_delete_error():
    """preset delete handles not found error."""
    mock_svc = MagicMock()
    mock_svc.delete.side_effect = PresetError("not found")
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "delete", "test", "--confirm"])
        assert result.exit_code != 0


# =============================================================================
# Preset CLI — apply command
# =============================================================================


def test_preset_apply_load_error():
    """preset apply handles missing preset."""
    mock_svc = MagicMock()
    mock_svc.load.side_effect = PresetError("not found")
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "apply", "missing"])
        assert result.exit_code != 0


def test_preset_apply_pod_create_error():
    """preset apply pod handles create error."""
    from rpctl.models.preset import Preset, PresetMetadata

    mock_svc = MagicMock()
    mock_svc.load.return_value = Preset(
        metadata=PresetMetadata(name="test", resource_type="pod"),
        params={"image_name": "img"},
    )
    mock_pod_svc = MagicMock()
    mock_pod_svc.create_pod.side_effect = ApiError("create failed")
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_pod_service", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["preset", "apply", "test"])
        assert result.exit_code != 0


def test_preset_apply_endpoint_create_error():
    """preset apply endpoint handles create error."""
    from rpctl.models.preset import Preset, PresetMetadata

    mock_svc = MagicMock()
    mock_svc.load.return_value = Preset(
        metadata=PresetMetadata(name="test", resource_type="endpoint"),
        params={"name": "ep", "template_id": "t1"},
    )
    mock_ep_svc = MagicMock()
    mock_ep_svc.create_endpoint.side_effect = ApiError("create failed")
    with (
        _preset_svc_ctx(mock_svc),
        patch("rpctl.cli.preset._get_endpoint_service", return_value=mock_ep_svc),
    ):
        result = runner.invoke(app, ["preset", "apply", "test"])
        assert result.exit_code != 0


def test_preset_apply_unknown_type():
    """preset apply handles unknown resource type in preset file."""
    from rpctl.models.preset import Preset, PresetMetadata

    mock_svc = MagicMock()
    # Create a preset with valid type then monkey-patch it
    preset = Preset(
        metadata=PresetMetadata(name="test", resource_type="pod"),
        params={"image_name": "img"},
    )
    preset.metadata.resource_type = "unknown"  # bypass validation
    mock_svc.load.return_value = preset
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(app, ["preset", "apply", "test"])
        assert result.exit_code == 1


def test_preset_apply_with_overrides():
    """preset apply passes CLI overrides."""
    from rpctl.models.preset import Preset, PresetMetadata

    mock_svc = MagicMock()
    mock_svc.load.return_value = Preset(
        metadata=PresetMetadata(name="test", resource_type="pod"),
        params={"image_name": "img"},
    )
    with _preset_svc_ctx(mock_svc):
        result = runner.invoke(
            app,
            ["preset", "apply", "test", "--dry-run", "--gpu-count", "4", "--workers-max", "10"],
        )
        assert result.exit_code == 0


# =============================================================================
# Endpoint CLI — remaining gaps
# =============================================================================


def test_endpoint_create_wrong_preset_type():
    """endpoint create rejects non-endpoint preset."""
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService as RealPresetService

    mock_preset_svc = MagicMock(spec=RealPresetService)
    mock_preset_svc.load.return_value = Preset(
        metadata=PresetMetadata(name="test", resource_type="pod"),
        params={"image_name": "img"},
    )
    mock_preset_svc.merge_preset_with_overrides = RealPresetService.merge_preset_with_overrides
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.services.preset_service.PresetService", return_value=mock_preset_svc),
    ):
        result = runner.invoke(
            app,
            ["endpoint", "create", "--preset", "test", "--name", "ep", "--template", "t1"],
        )
        assert result.exit_code == 1
        assert "not endpoint" in result.output


def test_endpoint_get_error():
    """endpoint get handles API error."""
    mock_ep_svc = MagicMock()
    mock_ep_svc.get_endpoint.side_effect = ApiError("not found", status_code=404)
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.endpoint_service.EndpointService", return_value=mock_ep_svc),
    ):
        result = runner.invoke(app, ["endpoint", "get", "ep-bad"])
        assert result.exit_code != 0


def test_endpoint_delete_confirm_prompt():
    """endpoint delete prompts for confirmation."""
    mock_ep_svc = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.endpoint_service.EndpointService", return_value=mock_ep_svc),
    ):
        # Abort at confirmation
        result = runner.invoke(app, ["endpoint", "delete", "ep-1"], input="n\n")
        assert result.exit_code != 0


# =============================================================================
# Pod CLI — remaining delete error path
# =============================================================================


def test_pod_delete_confirm_prompt():
    """pod delete prompts for confirmation."""
    mock_pod_svc = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["pod", "delete", "pod-1"], input="n\n")
        assert result.exit_code != 0


def test_pod_delete_api_error():
    """pod delete handles API error."""
    mock_pod_svc = MagicMock()
    mock_pod_svc.delete_pod.side_effect = ApiError("delete failed")
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["pod", "delete", "pod-1", "--confirm"])
        assert result.exit_code != 0


# =============================================================================
# Template / Volume CLI — delete confirmation prompts
# =============================================================================


def test_template_delete_confirm_prompt():
    """template delete prompts for confirmation."""
    mock_svc = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.template_service.TemplateService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["template", "delete", "tmpl-1"], input="n\n")
        assert result.exit_code != 0


def test_volume_delete_confirm_prompt():
    """volume delete prompts for confirmation."""
    mock_svc = MagicMock()
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.volume_service.VolumeService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["volume", "delete", "vol-1"], input="n\n")
        assert result.exit_code != 0
