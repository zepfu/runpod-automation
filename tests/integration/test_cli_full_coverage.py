"""Full coverage integration tests for all CLI command paths."""

from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from rpctl.errors import ApiError
from rpctl.main import app
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod
from rpctl.models.template import Template
from rpctl.models.volume import Volume
from typer.testing import CliRunner

runner = CliRunner()


def _mock_settings():
    mock = MagicMock()
    mock.api_key = "test-key"
    return mock


@contextmanager
def _svc_ctx(service_module, service_class, mock_svc):
    """Context manager for standard service mocking."""
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(f"rpctl.services.{service_module}.{service_class}", return_value=mock_svc),
    ):
        yield


# =============================================================================
# Pod CLI — uncovered paths
# =============================================================================


@pytest.fixture
def mock_pod_svc():
    pod = Pod(
        id="pod-001",
        name="test-pod",
        status="RUNNING",
        gpu_type="NVIDIA RTX A6000",
        gpu_count=1,
        image_name="runpod/pytorch:2.1",
        cost_per_hr=0.44,
    )
    svc = MagicMock()
    svc.list_pods.return_value = [pod]
    svc.get_pod.return_value = pod
    svc.create_pod.return_value = pod
    svc.stop_pod.return_value = {}
    svc.start_pod.return_value = {}
    svc.restart_pod.return_value = {}
    svc.delete_pod.return_value = {}
    return svc


def test_pod_start(mock_pod_svc):
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "start", "pod-001"])
        assert result.exit_code == 0
        assert "started" in result.output


def test_pod_stop(mock_pod_svc):
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "stop", "pod-001"])
        assert result.exit_code == 0
        assert "stopped" in result.output


def test_pod_restart(mock_pod_svc):
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "restart", "pod-001"])
        assert result.exit_code == 0
        assert "restarted" in result.output


def test_pod_get_json(mock_pod_svc):
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["--json", "pod", "get", "pod-001"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["id"] == "pod-001"


def test_pod_create_with_all_options():
    result = runner.invoke(
        app,
        [
            "pod",
            "create",
            "--image",
            "nvidia/cuda",
            "--name",
            "my-pod",
            "--gpu",
            "NVIDIA RTX A6000",
            "--gpu-count",
            "2",
            "--cloud-type",
            "secure",
            "--container-disk",
            "100",
            "--volume-disk",
            "50",
            "--volume-mount",
            "/data",
            "--ports",
            "8080/http",
            "--env",
            "FOO=bar",
            "--template",
            "tmpl-1",
            "--spot",
            "--region",
            "US-TX-3",
            "--min-vcpu",
            "4",
            "--min-ram",
            "16",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "nvidia/cuda" in result.output


def test_pod_create_with_cpu_options():
    result = runner.invoke(
        app,
        [
            "pod",
            "create",
            "--image",
            "python:3.12",
            "--cpu",
            "cpu3c",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "python:3.12" in result.output


def test_pod_create_with_network_volume():
    result = runner.invoke(
        app,
        [
            "pod",
            "create",
            "--image",
            "nvidia/cuda",
            "--network-volume",
            "vol-123",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0


def test_pod_create_invalid_env():
    result = runner.invoke(
        app,
        ["pod", "create", "--image", "test", "--env", "INVALID_NO_EQUALS", "--dry-run"],
    )
    assert result.exit_code != 0
    assert "KEY=VALUE" in result.output


def test_pod_create_live(mock_pod_svc):
    """Test pod create (non-dry-run) calls the service."""
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(
            app,
            ["pod", "create", "--image", "nvidia/cuda"],
        )
        assert result.exit_code == 0
        mock_pod_svc.create_pod.assert_called_once()


def test_pod_create_api_error(mock_pod_svc):
    mock_pod_svc.create_pod.side_effect = ApiError("boom", status_code=400)
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "create", "--image", "nvidia/cuda"])
        assert result.exit_code != 0


def test_pod_stop_api_error(mock_pod_svc):
    mock_pod_svc.stop_pod.side_effect = ApiError("boom", status_code=500)
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "stop", "pod-001"])
        assert result.exit_code != 0


def test_pod_start_api_error(mock_pod_svc):
    mock_pod_svc.start_pod.side_effect = ApiError("boom", status_code=500)
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "start", "pod-001"])
        assert result.exit_code != 0


def test_pod_restart_api_error(mock_pod_svc):
    mock_pod_svc.restart_pod.side_effect = ApiError("boom", status_code=500)
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "restart", "pod-001"])
        assert result.exit_code != 0


def test_pod_list_api_error(mock_pod_svc):
    mock_pod_svc.list_pods.side_effect = ApiError("boom")
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "list"])
        assert result.exit_code != 0


def test_pod_get_api_error(mock_pod_svc):
    mock_pod_svc.get_pod.side_effect = ApiError("boom")
    with _svc_ctx("pod_service", "PodService", mock_pod_svc):
        result = runner.invoke(app, ["pod", "get", "pod-001"])
        assert result.exit_code != 0


# =============================================================================
# Endpoint CLI — uncovered paths
# =============================================================================


@pytest.fixture
def mock_ep_svc():
    ep = Endpoint(
        id="ep-001",
        name="test-ep",
        gpu_ids="AMPERE_24",
        workers_min=0,
        workers_max=5,
        idle_timeout=10,
    )
    svc = MagicMock()
    svc.list_endpoints.return_value = [ep]
    svc.get_endpoint.return_value = ep
    svc.create_endpoint.return_value = ep
    svc.update_endpoint.return_value = ep
    svc.delete_endpoint.return_value = {}
    return svc


def test_endpoint_get(mock_ep_svc):
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(app, ["endpoint", "get", "ep-001"])
        assert result.exit_code == 0
        assert "ep-001" in result.output


def test_endpoint_get_json(mock_ep_svc):
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(app, ["--json", "endpoint", "get", "ep-001"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["id"] == "ep-001"


def test_endpoint_update(mock_ep_svc):
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(
            app,
            ["endpoint", "update", "ep-001", "--workers-max", "10"],
        )
        assert result.exit_code == 0


def test_endpoint_update_no_params():
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
    ):
        result = runner.invoke(app, ["endpoint", "update", "ep-001"])
        assert result.exit_code != 0


def test_endpoint_update_multiple_params(mock_ep_svc):
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(
            app,
            [
                "endpoint",
                "update",
                "ep-001",
                "--workers-min",
                "1",
                "--workers-max",
                "10",
                "--idle-timeout",
                "30",
                "--scaler-type",
                "QUEUE_DELAY",
                "--scaler-value",
                "8",
            ],
        )
        assert result.exit_code == 0


def test_endpoint_create_dry_run():
    result = runner.invoke(
        app,
        [
            "endpoint",
            "create",
            "--name",
            "my-ep",
            "--template",
            "tmpl-1",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "tmpl-1" in result.output


def test_endpoint_create_all_options():
    result = runner.invoke(
        app,
        [
            "endpoint",
            "create",
            "--name",
            "my-ep",
            "--template",
            "tmpl-1",
            "--gpu",
            "AMPERE_24",
            "--gpu-count",
            "2",
            "--workers-min",
            "1",
            "--workers-max",
            "10",
            "--idle-timeout",
            "30",
            "--scaler-type",
            "QUEUE_DELAY",
            "--scaler-value",
            "4",
            "--network-volume",
            "vol-1",
            "--flashboot",
            "--locations",
            "US-TX-3",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0


def test_endpoint_create_missing_name():
    result = runner.invoke(
        app,
        ["endpoint", "create", "--template", "tmpl-1", "--dry-run"],
    )
    assert result.exit_code != 0
    assert "name" in result.output.lower()


def test_endpoint_create_missing_template():
    result = runner.invoke(
        app,
        ["endpoint", "create", "--name", "my-ep", "--dry-run"],
    )
    assert result.exit_code != 0
    assert "template" in result.output.lower()


def test_endpoint_create_live(mock_ep_svc):
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(
            app,
            ["endpoint", "create", "--name", "my-ep", "--template", "tmpl-1"],
        )
        assert result.exit_code == 0
        mock_ep_svc.create_endpoint.assert_called_once()


def test_endpoint_create_api_error(mock_ep_svc):
    mock_ep_svc.create_endpoint.side_effect = ApiError("boom", status_code=400)
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(
            app,
            ["endpoint", "create", "--name", "my-ep", "--template", "tmpl-1"],
        )
        assert result.exit_code != 0


def test_endpoint_create_save_preset(tmp_path):
    with patch("rpctl.services.preset_service.get_config_dir", return_value=tmp_path):
        result = runner.invoke(
            app,
            [
                "endpoint",
                "create",
                "--name",
                "my-ep",
                "--template",
                "tmpl-1",
                "--save-preset",
                "my-ep-preset",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "my-ep-preset" in result.output


def test_endpoint_list_api_error(mock_ep_svc):
    mock_ep_svc.list_endpoints.side_effect = ApiError("boom")
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(app, ["endpoint", "list"])
        assert result.exit_code != 0


def test_endpoint_update_api_error(mock_ep_svc):
    mock_ep_svc.update_endpoint.side_effect = ApiError("boom")
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(
            app,
            ["endpoint", "update", "ep-001", "--workers-max", "10"],
        )
        assert result.exit_code != 0


def test_endpoint_delete_api_error(mock_ep_svc):
    mock_ep_svc.delete_endpoint.side_effect = ApiError("boom")
    with _svc_ctx("endpoint_service", "EndpointService", mock_ep_svc):
        result = runner.invoke(app, ["endpoint", "delete", "ep-001", "--confirm"])
        assert result.exit_code != 0


# =============================================================================
# Volume CLI — uncovered paths
# =============================================================================


@pytest.fixture
def mock_vol_svc():
    vol = Volume(
        id="vol-001",
        name="test-vol",
        size_gb=100,
        data_center_id="US-TX-3",
        used_size_gb=42.5,
    )
    svc = MagicMock()
    svc.list_volumes.return_value = [vol]
    svc.get_volume.return_value = vol
    svc.create_volume.return_value = vol
    svc.update_volume.return_value = vol
    svc.delete_volume.return_value = {}
    return svc


def test_volume_get(mock_vol_svc):
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(app, ["volume", "get", "vol-001"])
        assert result.exit_code == 0
        assert "vol-001" in result.output


def test_volume_create(mock_vol_svc):
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(
            app,
            ["volume", "create", "--name", "my-vol", "--size", "100", "--region", "US-TX-3"],
        )
        assert result.exit_code == 0


def test_volume_create_invalid_size():
    result = runner.invoke(
        app,
        ["volume", "create", "--name", "my-vol", "--size", "5000", "--region", "US-TX-3"],
    )
    assert result.exit_code != 0
    assert "4000" in result.output


def test_volume_update(mock_vol_svc):
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(
            app,
            ["volume", "update", "vol-001", "--name", "new-name"],
        )
        assert result.exit_code == 0


def test_volume_update_size(mock_vol_svc):
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(
            app,
            ["volume", "update", "vol-001", "--size", "200"],
        )
        assert result.exit_code == 0


def test_volume_update_no_params():
    result = runner.invoke(app, ["volume", "update", "vol-001"])
    assert result.exit_code != 0


def test_volume_create_api_error(mock_vol_svc):
    mock_vol_svc.create_volume.side_effect = ApiError("boom")
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(
            app,
            ["volume", "create", "--name", "my-vol", "--size", "100", "--region", "US-TX-3"],
        )
        assert result.exit_code != 0


def test_volume_get_api_error(mock_vol_svc):
    mock_vol_svc.get_volume.side_effect = ApiError("boom")
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(app, ["volume", "get", "vol-001"])
        assert result.exit_code != 0


def test_volume_update_api_error(mock_vol_svc):
    mock_vol_svc.update_volume.side_effect = ApiError("boom")
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(app, ["volume", "update", "vol-001", "--name", "x"])
        assert result.exit_code != 0


def test_volume_list_api_error(mock_vol_svc):
    mock_vol_svc.list_volumes.side_effect = ApiError("boom")
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(app, ["volume", "list"])
        assert result.exit_code != 0


def test_volume_delete_api_error(mock_vol_svc):
    mock_vol_svc.delete_volume.side_effect = ApiError("boom")
    with _svc_ctx("volume_service", "VolumeService", mock_vol_svc):
        result = runner.invoke(app, ["volume", "delete", "vol-001", "--confirm"])
        assert result.exit_code != 0


# =============================================================================
# Template CLI — uncovered paths
# =============================================================================


@pytest.fixture
def mock_tmpl_svc():
    tmpl = Template(
        id="tmpl-001",
        name="test-tmpl",
        image_name="runpod/pytorch:2.1",
        is_serverless=True,
    )
    svc = MagicMock()
    svc.list_templates.return_value = [tmpl]
    svc.get_template.return_value = tmpl
    svc.create_template.return_value = tmpl
    svc.update_template.return_value = tmpl
    svc.delete_template.return_value = {}
    return svc


def test_template_get(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(app, ["template", "get", "tmpl-001"])
        assert result.exit_code == 0
        assert "tmpl-001" in result.output


def test_template_create(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            ["template", "create", "--name", "my-tmpl", "--image", "pytorch:2.1"],
        )
        assert result.exit_code == 0


def test_template_create_all_options(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "--name",
                "my-tmpl",
                "--image",
                "pytorch:2.1",
                "--serverless",
                "--container-disk",
                "100",
                "--volume-disk",
                "50",
                "--ports",
                "8080/http",
                "--env",
                "FOO=bar",
                "--env",
                "BAZ=qux",
                "--readme",
                "My template",
            ],
        )
        assert result.exit_code == 0


def test_template_create_invalid_env(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            ["template", "create", "--name", "x", "--image", "x", "--env", "NOEQ"],
        )
        assert result.exit_code != 0
        assert "KEY=VALUE" in result.output


def test_template_update(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            ["template", "update", "tmpl-001", "--name", "new-name"],
        )
        assert result.exit_code == 0


def test_template_update_image(mock_tmpl_svc):
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            ["template", "update", "tmpl-001", "--image", "new-image"],
        )
        assert result.exit_code == 0


def test_template_update_no_params():
    result = runner.invoke(app, ["template", "update", "tmpl-001"])
    assert result.exit_code != 0


def test_template_create_api_error(mock_tmpl_svc):
    mock_tmpl_svc.create_template.side_effect = ApiError("boom")
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(
            app,
            ["template", "create", "--name", "x", "--image", "x"],
        )
        assert result.exit_code != 0


def test_template_get_api_error(mock_tmpl_svc):
    mock_tmpl_svc.get_template.side_effect = ApiError("boom")
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(app, ["template", "get", "tmpl-001"])
        assert result.exit_code != 0


def test_template_update_api_error(mock_tmpl_svc):
    mock_tmpl_svc.update_template.side_effect = ApiError("boom")
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(app, ["template", "update", "tmpl-001", "--name", "x"])
        assert result.exit_code != 0


def test_template_list_api_error(mock_tmpl_svc):
    mock_tmpl_svc.list_templates.side_effect = ApiError("boom")
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code != 0


def test_template_delete_api_error(mock_tmpl_svc):
    mock_tmpl_svc.delete_template.side_effect = ApiError("boom")
    with _svc_ctx("template_service", "TemplateService", mock_tmpl_svc):
        result = runner.invoke(app, ["template", "delete", "tmpl-001", "--confirm"])
        assert result.exit_code != 0


# =============================================================================
# Capacity CLI — uncovered paths
# =============================================================================


def test_capacity_compare(tmp_path):
    from rpctl.models.capacity import GpuType

    gpu1 = GpuType(id="A100", display_name="A100 80GB", memory_gb=80, max_gpu_count=8)
    gpu2 = GpuType(id="A6000", display_name="RTX A6000", memory_gb=48, max_gpu_count=4)
    mock_svc = MagicMock()
    mock_svc.list_gpu_types.return_value = [gpu1, gpu2]

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["capacity", "compare", "A100", "A6000"])
        assert result.exit_code == 0


def test_capacity_compare_too_few():
    result = runner.invoke(app, ["capacity", "compare", "A100"])
    assert result.exit_code != 0


def test_capacity_check_json():
    from rpctl.models.capacity import GpuAvailabilityDetail

    detail = GpuAvailabilityDetail(
        id="A100",
        display_name="A100 80GB",
        memory_gb=80,
    )
    mock_svc = MagicMock()
    mock_svc.check_gpu.return_value = detail

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["--json", "capacity", "check", "--gpu", "A100"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["id"] == "A100"


def test_capacity_regions_json():
    mock_svc = MagicMock()
    mock_svc.list_regions.return_value = []

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["--json", "capacity", "regions"])
        assert result.exit_code == 0


def test_capacity_list_error():
    mock_svc = MagicMock()
    mock_svc.list_gpu_types.side_effect = ApiError("boom")

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["capacity", "list"])
        assert result.exit_code != 0


def test_capacity_check_error():
    mock_svc = MagicMock()
    mock_svc.check_gpu.side_effect = ApiError("boom")

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["capacity", "check", "--gpu", "A100"])
        assert result.exit_code != 0


def test_capacity_regions_error():
    mock_svc = MagicMock()
    mock_svc.list_regions.side_effect = ApiError("boom")

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["capacity", "regions"])
        assert result.exit_code != 0


def test_capacity_compare_error():
    mock_svc = MagicMock()
    mock_svc.list_gpu_types.side_effect = ApiError("boom")

    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.graphql_client.GraphQLClient", return_value=MagicMock()),
        patch("rpctl.services.capacity_service.CapacityService", return_value=mock_svc),
    ):
        result = runner.invoke(app, ["capacity", "compare", "A100", "A6000"])
        assert result.exit_code != 0


# =============================================================================
# Config CLI — uncovered paths
# =============================================================================


def test_config_show(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with (
        patch("rpctl.config.settings.Settings.load", return_value=settings),
        patch("rpctl.config.settings.Settings.has_api_key", return_value=True),
    ):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0


def test_config_show_json(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with (
        patch("rpctl.config.settings.Settings.load", return_value=settings),
        patch("rpctl.config.settings.Settings.has_api_key", return_value=False),
    ):
        result = runner.invoke(app, ["--json", "config", "show"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "active_profile" in parsed


def test_config_list_profiles(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["config", "list-profiles"])
        assert result.exit_code == 0
        assert "default" in result.output


def test_config_list_profiles_json(tmp_path):
    from rpctl.config.settings import Settings

    settings = Settings.create_default()
    settings._config_path = tmp_path / "config.yaml"
    settings.save()

    with patch("rpctl.config.settings.Settings.load", return_value=settings):
        result = runner.invoke(app, ["--json", "config", "list-profiles"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "profiles" in parsed


# =============================================================================
# Preset CLI — uncovered paths (apply non-dry-run, endpoint apply)
# =============================================================================


def test_preset_apply_pod_live(tmp_path, mock_pod_svc):
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    svc = PresetService(presets_dir=tmp_path / "presets")
    svc.save(
        Preset(
            metadata=PresetMetadata(name="live-pod", resource_type="pod", source="cli"),
            params={"image_name": "nvidia/cuda", "gpu_count": 1},
        )
    )

    with (
        patch("rpctl.cli.preset._get_preset_service", return_value=svc),
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_svc),
    ):
        result = runner.invoke(app, ["preset", "apply", "live-pod"])
        assert result.exit_code == 0


def test_preset_apply_endpoint_dry_run(tmp_path):
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    svc = PresetService(presets_dir=tmp_path / "presets")
    svc.save(
        Preset(
            metadata=PresetMetadata(name="ep-preset", resource_type="endpoint", source="cli"),
            params={"name": "ep", "template_id": "tmpl-1", "gpu_ids": "AMPERE_24"},
        )
    )

    with patch("rpctl.cli.preset._get_preset_service", return_value=svc):
        result = runner.invoke(app, ["preset", "apply", "ep-preset", "--dry-run"])
        assert result.exit_code == 0
        assert "tmpl-1" in result.output


def test_preset_apply_endpoint_live(tmp_path, mock_ep_svc):
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    svc = PresetService(presets_dir=tmp_path / "presets")
    svc.save(
        Preset(
            metadata=PresetMetadata(name="ep-live", resource_type="endpoint", source="cli"),
            params={"name": "ep", "template_id": "tmpl-1", "gpu_ids": "AMPERE_24"},
        )
    )

    with (
        patch("rpctl.cli.preset._get_preset_service", return_value=svc),
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.endpoint_service.EndpointService", return_value=mock_ep_svc),
    ):
        result = runner.invoke(app, ["preset", "apply", "ep-live"])
        assert result.exit_code == 0


def test_preset_apply_unknown_type(tmp_path):
    """Preset with unknown resource_type should fail."""
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    svc = PresetService(presets_dir=tmp_path / "presets")
    # Manually write a preset with invalid type
    p = Preset(
        metadata=PresetMetadata(name="bad-type", resource_type="pod", source="cli"),
        params={"image_name": "test"},
    )
    path = svc.save(p)
    # Hack the file to have an invalid resource_type
    import yaml

    data = yaml.safe_load(path.read_text())
    data["metadata"]["resource_type"] = "unknown"
    path.write_text(yaml.safe_dump(data))

    with patch("rpctl.cli.preset._get_preset_service", return_value=svc):
        result = runner.invoke(app, ["preset", "apply", "bad-type", "--dry-run"])
        assert result.exit_code != 0


def test_preset_apply_with_overrides(tmp_path):
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    svc = PresetService(presets_dir=tmp_path / "presets")
    svc.save(
        Preset(
            metadata=PresetMetadata(name="override-test", resource_type="pod", source="cli"),
            params={"image_name": "nvidia/cuda", "gpu_count": 1},
        )
    )

    with patch("rpctl.cli.preset._get_preset_service", return_value=svc):
        result = runner.invoke(
            app,
            [
                "preset",
                "apply",
                "override-test",
                "--gpu-count",
                "4",
                "--name",
                "custom-name",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "4" in result.output
