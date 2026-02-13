"""Tests for rpctl ssh command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rpctl.cli.ssh import _build_ssh_command, _resolve_ssh_info
from rpctl.errors import RpctlError
from rpctl.models.pod import Pod


def _make_pod(status="RUNNING", runtime=None) -> Pod:
    return Pod(
        id="pod-abc123",
        name="my-gpu-pod",
        status=status,
        gpu_type="A6000",
        gpu_count=1,
        image_name="nvidia/cuda",
        runtime=runtime or {},
    )


# --- _resolve_ssh_info ---


def test_resolve_ssh_info_from_runtime_ports():
    """Extract SSH host/port from runtime ports list."""
    pod = _make_pod(
        runtime={
            "ports": [
                {"ip": "1.2.3.4", "privatePort": 8888, "publicPort": 8888, "type": "http"},
                {"ip": "1.2.3.4", "privatePort": 22, "publicPort": 54321, "type": "tcp"},
            ],
        },
    )
    host, port = _resolve_ssh_info(pod)
    assert host == "1.2.3.4"
    assert port == 54321


def test_resolve_ssh_info_fallback_proxy():
    """Falls back to proxy hostname when no ports in runtime."""
    pod = _make_pod(runtime={})
    host, port = _resolve_ssh_info(pod)
    assert host == "pod-abc123-ssh.proxy.runpod.net"
    assert port == 22


def test_resolve_ssh_info_no_runtime():
    """Falls back when runtime is None."""
    pod = _make_pod()
    pod.runtime = {}
    host, port = _resolve_ssh_info(pod)
    assert host == "pod-abc123-ssh.proxy.runpod.net"
    assert port == 22


def test_resolve_ssh_info_ports_no_ssh():
    """Falls back when ports exist but none for port 22."""
    pod = _make_pod(
        runtime={
            "ports": [
                {"ip": "1.2.3.4", "privatePort": 8888, "publicPort": 8888, "type": "http"},
            ],
        },
    )
    host, port = _resolve_ssh_info(pod)
    assert host == "pod-abc123-ssh.proxy.runpod.net"
    assert port == 22


def test_resolve_ssh_info_no_ip_in_port():
    """Falls back when port 22 exists but IP is empty."""
    pod = _make_pod(
        runtime={
            "ports": [
                {"ip": "", "privatePort": 22, "publicPort": 12345, "type": "tcp"},
            ],
        },
    )
    host, port = _resolve_ssh_info(pod)
    assert host == "pod-abc123-ssh.proxy.runpod.net"
    assert port == 22


# --- _build_ssh_command ---


def test_build_ssh_command_basic():
    cmd = _build_ssh_command("1.2.3.4", 22)
    assert cmd[0] == "ssh"
    assert "-p" in cmd
    assert "22" in cmd
    assert "root@1.2.3.4" in cmd


def test_build_ssh_command_custom_user():
    cmd = _build_ssh_command("1.2.3.4", 22, user="ubuntu")
    assert "ubuntu@1.2.3.4" in cmd


def test_build_ssh_command_custom_port():
    cmd = _build_ssh_command("1.2.3.4", 54321)
    idx = cmd.index("-p")
    assert cmd[idx + 1] == "54321"


def test_build_ssh_command_with_key():
    cmd = _build_ssh_command("1.2.3.4", 22, key_file="/home/user/.ssh/id_rsa")
    assert "-i" in cmd
    assert "/home/user/.ssh/id_rsa" in cmd


def test_build_ssh_command_with_remote_command():
    cmd = _build_ssh_command("1.2.3.4", 22, remote_command="nvidia-smi")
    assert cmd[-1] == "nvidia-smi"


def test_build_ssh_command_strict_host_checking_disabled():
    cmd = _build_ssh_command("1.2.3.4", 22)
    assert "StrictHostKeyChecking=no" in cmd
    assert "UserKnownHostsFile=/dev/null" in cmd


# --- CLI integration ---


def test_ssh_connect_dry_run():
    """--dry-run prints the SSH command without executing."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    mock_pod = _make_pod(
        runtime={
            "ports": [
                {"ip": "5.6.7.8", "privatePort": 22, "publicPort": 11111, "type": "tcp"},
            ],
        },
    )

    with patch("rpctl.cli.ssh._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_pod.return_value = mock_pod
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["ssh", "connect", "pod-abc123", "--dry-run"])
        assert result.exit_code == 0
        assert "ssh" in result.output
        assert "5.6.7.8" in result.output
        assert "11111" in result.output


def test_ssh_connect_not_running():
    """Error when pod is not running."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    mock_pod = _make_pod(status="EXITED")

    with patch("rpctl.cli.ssh._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_pod.return_value = mock_pod
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["ssh", "connect", "pod-abc123"])
        assert result.exit_code == 1
        assert "not running" in result.output


def test_ssh_connect_api_error():
    """Error when pod fetch fails."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()

    with patch("rpctl.cli.ssh._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.get_pod.side_effect = RpctlError("Pod not found")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["ssh", "connect", "pod-xyz"])
        assert result.exit_code == 1


def test_ssh_connect_execvp_called():
    """Verify os.execvp is called with the right SSH command."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    mock_pod = _make_pod(
        runtime={
            "ports": [
                {"ip": "10.0.0.1", "privatePort": 22, "publicPort": 22222, "type": "tcp"},
            ],
        },
    )

    with (
        patch("rpctl.cli.ssh._get_pod_service") as mock_svc_fn,
        patch("rpctl.cli.ssh.os.execvp") as mock_exec,
    ):
        mock_svc = MagicMock()
        mock_svc.get_pod.return_value = mock_pod
        mock_svc_fn.return_value = mock_svc

        runner.invoke(app, ["ssh", "connect", "pod-abc123"])
        mock_exec.assert_called_once()
        args = mock_exec.call_args
        assert args[0][0] == "ssh"
        cmd_list = args[0][1]
        assert "root@10.0.0.1" in cmd_list
        assert "22222" in cmd_list


def test_ssh_connect_with_options():
    """Verify --user, --key, --command options are passed through."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    runtime = {"ports": [{"ip": "1.1.1.1", "privatePort": 22, "publicPort": 22}]}
    mock_pod = _make_pod(runtime=runtime)

    with (
        patch("rpctl.cli.ssh._get_pod_service") as mock_svc_fn,
        patch("rpctl.cli.ssh.os.execvp") as mock_exec,
    ):
        mock_svc = MagicMock()
        mock_svc.get_pod.return_value = mock_pod
        mock_svc_fn.return_value = mock_svc

        runner.invoke(
            app,
            [
                "ssh",
                "connect",
                "pod-abc123",
                "--user",
                "ubuntu",
                "--key",
                "/tmp/key.pem",
                "--command",
                "nvidia-smi",
            ],
        )
        mock_exec.assert_called_once()
        cmd_list = mock_exec.call_args[0][1]
        assert "ubuntu@1.1.1.1" in cmd_list
        assert "/tmp/key.pem" in cmd_list
        assert "nvidia-smi" in cmd_list
