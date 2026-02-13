"""Tests for pod wait command and new pod create parameters."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rpctl.errors import RpctlError
from rpctl.models.pod import Pod, PodCreateParams
from rpctl.services.poll import PollTimeoutError

# --- PodCreateParams.to_sdk_kwargs() mapping ---


def test_to_sdk_kwargs_docker_start_cmd():
    """docker_start_cmd is passed through to SDK kwargs."""
    params = PodCreateParams(
        image_name="test",
        docker_start_cmd="python handler.py",
    )
    kwargs = params.to_sdk_kwargs()
    assert kwargs["docker_start_cmd"] == "python handler.py"


def test_to_sdk_kwargs_docker_entrypoint():
    """docker_entrypoint maps to docker_args in SDK kwargs."""
    params = PodCreateParams(
        image_name="test",
        docker_entrypoint="/bin/bash -c",
    )
    kwargs = params.to_sdk_kwargs()
    assert kwargs["docker_args"] == "/bin/bash -c"


def test_to_sdk_kwargs_allowed_cuda_versions():
    """allowed_cuda_versions is passed through to SDK kwargs."""
    params = PodCreateParams(
        image_name="test",
        allowed_cuda_versions=["11.8", "12.1"],
    )
    kwargs = params.to_sdk_kwargs()
    assert kwargs["allowed_cuda_versions"] == ["11.8", "12.1"]


def test_to_sdk_kwargs_support_public_ip():
    """support_public_ip is passed through when True."""
    params = PodCreateParams(
        image_name="test",
        support_public_ip=True,
    )
    kwargs = params.to_sdk_kwargs()
    assert kwargs["support_public_ip"] is True


def test_to_sdk_kwargs_no_optional_fields():
    """Optional fields are not included when empty/default."""
    params = PodCreateParams(image_name="test")
    kwargs = params.to_sdk_kwargs()
    assert "docker_start_cmd" not in kwargs
    assert "docker_args" not in kwargs
    assert "allowed_cuda_versions" not in kwargs
    assert "support_public_ip" not in kwargs


# --- PodService.wait_until_running() ---


def _make_pod(status: str = "RUNNING") -> Pod:
    return Pod(
        id="pod-123",
        name="test-pod",
        status=status,
        gpu_type="A100",
        gpu_count=1,
        image_name="nvidia/cuda",
    )


def test_pod_service_wait_immediate():
    """wait_until_running returns immediately if already running."""
    from rpctl.services.pod_service import PodService

    mock_client = MagicMock()
    mock_client.get_pod.return_value = {
        "id": "pod-123",
        "name": "test",
        "imageName": "test",
        "desiredStatus": "RUNNING",
        "runtime": {"status": "RUNNING"},
    }
    svc = PodService(mock_client)
    pod = svc.wait_until_running("pod-123", timeout=10, interval=0.01)
    assert pod.status == "RUNNING"
    assert mock_client.get_pod.call_count == 1


def test_pod_service_wait_transitions():
    """wait_until_running polls until RUNNING status."""
    from rpctl.services.pod_service import PodService

    mock_client = MagicMock()
    mock_client.get_pod.side_effect = [
        {"id": "pod-123", "name": "test", "imageName": "x", "runtime": {"status": "CREATED"}},
        {"id": "pod-123", "name": "test", "imageName": "x", "runtime": {"status": "PULLING"}},
        {"id": "pod-123", "name": "test", "imageName": "x", "runtime": {"status": "RUNNING"}},
    ]
    svc = PodService(mock_client)
    pod = svc.wait_until_running("pod-123", timeout=10, interval=0.01)
    assert pod.status == "RUNNING"
    assert mock_client.get_pod.call_count == 3


def test_pod_service_wait_timeout():
    """wait_until_running raises PollTimeoutError on timeout."""
    from rpctl.services.pod_service import PodService

    mock_client = MagicMock()
    mock_client.get_pod.return_value = {
        "id": "pod-123",
        "name": "test",
        "imageName": "x",
        "runtime": {"status": "CREATED"},
    }
    svc = PodService(mock_client)
    with pytest.raises(PollTimeoutError):
        svc.wait_until_running("pod-123", timeout=0.05, interval=0.01)


# --- CLI: rpctl pod wait ---


def test_cli_pod_wait_success():
    """rpctl pod wait POD_ID succeeds when pod is running."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_running.return_value = _make_pod("RUNNING")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app, ["pod", "wait", "pod-123", "--timeout", "60", "--interval", "2"]
        )
        assert result.exit_code == 0
        mock_svc.wait_until_running.assert_called_once_with("pod-123", timeout=60, interval=2)


def test_cli_pod_wait_timeout():
    """rpctl pod wait exits 2 on timeout."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_running.side_effect = PollTimeoutError("timed out")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "wait", "pod-123"])
        assert result.exit_code == 2


def test_cli_pod_wait_api_error():
    """rpctl pod wait exits 1 on API error."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_running.side_effect = RpctlError("Not found")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "wait", "pod-bad"])
        assert result.exit_code == 1


# --- CLI: rpctl pod create with new flags ---


def test_cli_pod_create_docker_start_cmd():
    """--docker-start-cmd is passed through to create."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_pod.return_value = _make_pod()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "test",
                "--docker-start-cmd",
                "python handler.py",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_svc.create_pod.call_args[0][0]
        assert call_args.docker_start_cmd == "python handler.py"


def test_cli_pod_create_entrypoint():
    """--entrypoint is passed through to create."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_pod.return_value = _make_pod()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            ["pod", "create", "--image", "test", "--entrypoint", "/bin/bash -c"],
        )
        assert result.exit_code == 0
        call_args = mock_svc.create_pod.call_args[0][0]
        assert call_args.docker_entrypoint == "/bin/bash -c"


def test_cli_pod_create_public_ip():
    """--public-ip sets support_public_ip=True."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_pod.return_value = _make_pod()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            ["pod", "create", "--image", "test", "--public-ip"],
        )
        assert result.exit_code == 0
        call_args = mock_svc.create_pod.call_args[0][0]
        assert call_args.support_public_ip is True


def test_cli_pod_create_cuda_versions():
    """--cuda-version is repeatable and passed through."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_pod.return_value = _make_pod()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "test",
                "--cuda-version",
                "11.8",
                "--cuda-version",
                "12.1",
            ],
        )
        assert result.exit_code == 0
        call_args = mock_svc.create_pod.call_args[0][0]
        assert call_args.allowed_cuda_versions == ["11.8", "12.1"]
