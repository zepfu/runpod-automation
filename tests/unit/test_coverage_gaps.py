"""Tests for remaining coverage gaps across models, errors, settings, services."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import yaml
from rpctl.errors import AuthenticationError, ResourceNotFoundError
from rpctl.models.endpoint import EndpointCreateParams
from rpctl.models.pod import PodCreateParams

# --- errors.py: is_transient properties ---


def test_auth_error_is_transient():
    err = AuthenticationError("bad key")
    assert err.is_transient is False


def test_not_found_error_is_transient():
    err = ResourceNotFoundError("missing", status_code=404)
    assert err.is_transient is False


# --- PodCreateParams.to_sdk_kwargs edge cases ---


def test_pod_params_gpu_type_id():
    p = PodCreateParams(image_name="img", gpu_type_id="A100")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["gpu_type_id"] == "A100"


def test_pod_params_network_volume():
    p = PodCreateParams(image_name="img", network_volume_id="vol-1")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["network_volume_id"] == "vol-1"


def test_pod_params_docker_entrypoint():
    p = PodCreateParams(image_name="img", docker_entrypoint="bash -c 'echo hi'")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["docker_args"] == "bash -c 'echo hi'"


def test_pod_params_template_id():
    p = PodCreateParams(image_name="img", template_id="tmpl-1")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["template_id"] == "tmpl-1"


def test_pod_params_support_public_ip():
    p = PodCreateParams(image_name="img", support_public_ip=True)
    kwargs = p.to_sdk_kwargs()
    assert kwargs["support_public_ip"] is True


def test_pod_params_interruptible():
    p = PodCreateParams(image_name="img", interruptible=True)
    kwargs = p.to_sdk_kwargs()
    assert kwargs["bid_per_gpu"] == 0.0


def test_pod_params_data_center_ids():
    p = PodCreateParams(image_name="img", data_center_ids=["US-TX-3"])
    kwargs = p.to_sdk_kwargs()
    assert kwargs["data_center_id"] == "US-TX-3"


# --- EndpointCreateParams.to_sdk_kwargs edge cases ---


def test_endpoint_params_network_volume():
    p = EndpointCreateParams(name="ep", template_id="t1", network_volume_id="vol-1")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["network_volume_id"] == "vol-1"


def test_endpoint_params_flashboot():
    p = EndpointCreateParams(name="ep", template_id="t1", flashboot=True)
    kwargs = p.to_sdk_kwargs()
    assert kwargs["flashboot"] is True


def test_endpoint_params_locations():
    p = EndpointCreateParams(name="ep", template_id="t1", locations="US-TX-3,EU-RO-1")
    kwargs = p.to_sdk_kwargs()
    assert kwargs["locations"] == "US-TX-3,EU-RO-1"


# --- Settings: XDG path and keyring API key ---


def test_get_config_dir_xdg(tmp_path):
    from rpctl.config.settings import get_config_dir

    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
        result = get_config_dir()
        assert result == tmp_path / "rpctl"


def test_api_key_from_keyring(tmp_path):
    import sys

    from rpctl.config.settings import Settings

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"active_profile": "default", "profiles": {"default": {}}}))
    settings = Settings.load(config_path=config_file)

    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = "keyring-key"
    env = {k: v for k, v in os.environ.items() if k != "RUNPOD_API_KEY"}
    with (
        patch.dict(os.environ, env, clear=True),
        patch.dict(sys.modules, {"keyring": mock_keyring}),
    ):
        assert settings.api_key == "keyring-key"


# --- CapacityService: available_only filter and list_cpu_types ---


def test_capacity_available_only_filter():
    from rpctl.services.capacity_service import CapacityService

    gql = MagicMock()
    gql.execute.return_value = {
        "gpuTypes": [
            {
                "id": "A100",
                "displayName": "A100 80GB",
                "memoryInGb": 80,
                "maxGpuCount": 8,
                "secureCloud": True,
                "communityCloud": True,
                "lowestPrice": {
                    "minimumBidPrice": 0.5,
                    "stockStatus": "High",
                },
                "communityPrice": 1.5,
                "securePrice": 2.0,
            },
            {
                "id": "V100",
                "displayName": "V100 16GB",
                "memoryInGb": 16,
                "maxGpuCount": 8,
                "secureCloud": True,
                "communityCloud": True,
                "lowestPrice": {
                    "minimumBidPrice": 0.3,
                    "stockStatus": "Unavailable",
                },
                "communityPrice": 0.5,
                "securePrice": 0.8,
            },
        ]
    }
    svc = CapacityService(gql)
    result = svc.list_gpu_types(available_only=True)
    assert len(result) == 1
    assert result[0].id == "A100"


def test_capacity_list_cpu_types():
    from rpctl.services.capacity_service import CapacityService

    gql = MagicMock()
    gql.execute.return_value = {
        "cpuTypes": [
            {
                "id": "cpu-1",
                "displayName": "CPU Small",
                "vcpuCount": 2,
                "memoryInGb": 4,
                "pricePerVcpuHr": 0.01,
            },
        ]
    }
    svc = CapacityService(gql)
    result = svc.list_cpu_types()
    assert len(result) == 1
    assert result[0].id == "cpu-1"


# --- PresetService: malformed file skip ---


def test_preset_list_skips_malformed(tmp_path):
    from rpctl.services.preset_service import PresetService

    presets_dir = tmp_path / "presets"
    presets_dir.mkdir()

    # Write a valid preset
    valid = {
        "metadata": {"name": "good", "resource_type": "pod"},
        "params": {"image_name": "test"},
    }
    (presets_dir / "good.yaml").write_text(yaml.dump(valid))

    # Write a malformed preset
    (presets_dir / "bad.yaml").write_text("not: valid: yaml: [[[")

    svc = PresetService(presets_dir=presets_dir)
    result = svc.list_presets()
    assert len(result) == 1
    assert result[0].metadata.name == "good"


# --- main.py: no subcommand prints help ---


def test_main_no_subcommand():
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    # With no_args_is_help=True, typer shows help and exits
    result = runner.invoke(app, [])
    assert "rpctl" in result.output or result.exit_code == 0


def test_main_verbose_no_subcommand():
    """Verbose flag with no subcommand still prints help."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(app, ["--verbose"])
    # Should get help output or exit cleanly
    assert result.exit_code == 0 or "rpctl" in result.output


def test_main_version():
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "rpctl" in result.output


# --- preset CLI: _get_preset_service default path ---


def test_get_preset_service_default():
    """_get_preset_service with no args uses default dir."""
    from rpctl.cli.preset import _get_preset_service

    svc = _get_preset_service()
    assert svc is not None


# --- preset delete confirmation prompt ---


def test_preset_delete_prompt_abort():
    """preset delete aborts on 'n' input."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    mock_svc = MagicMock()
    with patch("rpctl.cli.preset._get_preset_service", return_value=mock_svc):
        result = runner.invoke(app, ["preset", "delete", "test"], input="n\n")
        assert result.exit_code != 0
        mock_svc.delete.assert_not_called()
