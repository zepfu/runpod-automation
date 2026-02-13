"""Integration tests for Phase 2 CLI commands (pod, endpoint, volume, template)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rpctl.main import app
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod
from rpctl.models.template import Template
from rpctl.models.volume import Volume

runner = CliRunner()


def _mock_settings():
    mock = MagicMock()
    mock.api_key = "test-key"
    return mock


# --- Pod tests ---


@pytest.fixture
def mock_pod_service():
    pods = [
        Pod(
            id="pod-001",
            name="test-pod",
            status="RUNNING",
            gpu_type="NVIDIA RTX A6000",
            gpu_count=1,
            image_name="runpod/pytorch:2.1",
            cost_per_hr=0.44,
        ),
    ]
    svc = MagicMock()
    svc.list_pods.return_value = pods
    svc.get_pod.return_value = pods[0]
    svc.create_pod.return_value = pods[0]
    return svc


def test_pod_help():
    result = runner.invoke(app, ["pod", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "list" in result.output
    assert "delete" in result.output


def test_pod_list(mock_pod_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_service),
    ):
        result = runner.invoke(app, ["pod", "list"])
        assert result.exit_code == 0
        assert "pod-001" in result.output
        assert "test-pod" in result.output


def test_pod_list_json(mock_pod_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_service),
    ):
        result = runner.invoke(app, ["--json", "pod", "list"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert parsed[0]["id"] == "pod-001"


def test_pod_get(mock_pod_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_service),
    ):
        result = runner.invoke(app, ["pod", "get", "pod-001"])
        assert result.exit_code == 0
        assert "pod-001" in result.output


def test_pod_delete_with_confirm(mock_pod_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch("rpctl.services.pod_service.PodService", return_value=mock_pod_service),
    ):
        result = runner.invoke(app, ["pod", "delete", "pod-001", "--confirm"])
        assert result.exit_code == 0
        assert "deleted" in result.output


def test_pod_create_dry_run():
    result = runner.invoke(
        app,
        ["pod", "create", "--image", "nvidia/cuda", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "nvidia/cuda" in result.output


# --- Endpoint tests ---


@pytest.fixture
def mock_endpoint_service():
    endpoints = [
        Endpoint(
            id="ep-001",
            name="test-endpoint",
            gpu_ids="AMPERE_24",
            workers_min=0,
            workers_max=5,
            idle_timeout=10,
        ),
    ]
    svc = MagicMock()
    svc.list_endpoints.return_value = endpoints
    svc.get_endpoint.return_value = endpoints[0]
    svc.create_endpoint.return_value = endpoints[0]
    svc.update_endpoint.return_value = endpoints[0]
    return svc


def test_endpoint_list(mock_endpoint_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.endpoint_service.EndpointService",
            return_value=mock_endpoint_service,
        ),
    ):
        result = runner.invoke(app, ["endpoint", "list"])
        assert result.exit_code == 0
        assert "ep-001" in result.output


def test_endpoint_delete_with_confirm(mock_endpoint_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.endpoint_service.EndpointService",
            return_value=mock_endpoint_service,
        ),
    ):
        result = runner.invoke(app, ["endpoint", "delete", "ep-001", "--confirm"])
        assert result.exit_code == 0
        assert "deleted" in result.output


# --- Volume tests ---


@pytest.fixture
def mock_volume_service():
    volumes = [
        Volume(
            id="vol-001",
            name="test-volume",
            size_gb=100,
            data_center_id="US-TX-3",
            used_size_gb=42.5,
        ),
    ]
    svc = MagicMock()
    svc.list_volumes.return_value = volumes
    svc.get_volume.return_value = volumes[0]
    svc.create_volume.return_value = volumes[0]
    return svc


def test_volume_list(mock_volume_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.volume_service.VolumeService",
            return_value=mock_volume_service,
        ),
    ):
        result = runner.invoke(app, ["volume", "list"])
        assert result.exit_code == 0
        assert "vol-001" in result.output


def test_volume_delete_with_confirm(mock_volume_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.volume_service.VolumeService",
            return_value=mock_volume_service,
        ),
    ):
        result = runner.invoke(app, ["volume", "delete", "vol-001", "--confirm"])
        assert result.exit_code == 0
        assert "deleted" in result.output


# --- Template tests ---


@pytest.fixture
def mock_template_service():
    templates = [
        Template(
            id="tmpl-001",
            name="test-template",
            image_name="runpod/pytorch:2.1",
            is_serverless=True,
        ),
    ]
    svc = MagicMock()
    svc.list_templates.return_value = templates
    svc.get_template.return_value = templates[0]
    svc.create_template.return_value = templates[0]
    return svc


def test_template_list(mock_template_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.template_service.TemplateService",
            return_value=mock_template_service,
        ),
    ):
        result = runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0
        assert "tmpl-001" in result.output


def test_template_delete_with_confirm(mock_template_service):
    with (
        patch("rpctl.config.settings.Settings.load", return_value=_mock_settings()),
        patch("rpctl.api.rest_client.RestClient", return_value=MagicMock()),
        patch(
            "rpctl.services.template_service.TemplateService",
            return_value=mock_template_service,
        ),
    ):
        result = runner.invoke(app, ["template", "delete", "tmpl-001", "--confirm"])
        assert result.exit_code == 0
        assert "deleted" in result.output
