"""Tests for pod stop-all and delete-all CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.errors import RpctlError
from rpctl.main import app
from rpctl.models.pod import Pod

runner = CliRunner()


def _make_pod(pod_id: str, name: str = "test", status: str = "RUNNING") -> Pod:
    return Pod(
        id=pod_id,
        name=name,
        status=status,
        gpu_type="A100",
        gpu_count=1,
        image_name="nvidia/cuda",
    )


# --- stop-all ---


def test_stop_all_no_pods():
    """stop-all with no running pods prints message and exits 0."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = []
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "stop-all", "--confirm"])
        assert result.exit_code == 0
        assert "No running pods" in result.output


def test_stop_all_confirm_sequential():
    """stop-all --confirm stops pods sequentially."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.stop_pod.return_value = {}
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "stop-all", "--confirm"])
        assert result.exit_code == 0
        assert mock_svc.stop_pod.call_count == 2


def test_stop_all_sequential_error():
    """stop-all sequential prints error for individual pod failures."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.stop_pod.side_effect = [None, RpctlError("fail")]
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "stop-all", "--confirm"])
        assert "Failed to stop" in result.output


def test_stop_all_parallel():
    """stop-all --parallel --confirm uses parallel_map."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        pods = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.list_pods.return_value = pods
        mock_svc_fn.return_value = mock_svc

        with patch("rpctl.services.parallel.parallel_map") as mock_parallel:
            mock_result = MagicMock()
            mock_result.succeeded = [({}, _make_pod("p1")), ({}, _make_pod("p2"))]
            mock_result.failed = []
            mock_parallel.return_value = mock_result

            result = runner.invoke(app, ["pod", "stop-all", "--confirm", "--parallel"])
            assert result.exit_code == 0
            mock_parallel.assert_called_once()


def test_stop_all_parallel_with_failures():
    """stop-all --parallel exits 1 when some pods fail."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        pods = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.list_pods.return_value = pods
        mock_svc_fn.return_value = mock_svc

        with patch("rpctl.services.parallel.parallel_map") as mock_parallel:
            mock_result = MagicMock()
            mock_result.succeeded = [({}, _make_pod("p1"))]
            mock_result.failed = [(_make_pod("p2"), Exception("timeout"))]
            mock_parallel.return_value = mock_result

            result = runner.invoke(app, ["pod", "stop-all", "--confirm", "--parallel"])
            assert result.exit_code == 1


def test_stop_all_api_error():
    """stop-all exits 1 on API error during list."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.side_effect = RpctlError("API down")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "stop-all", "--confirm"])
        assert result.exit_code == 1


def test_stop_all_prompt_abort():
    """stop-all without --confirm prompts and aborts on 'n'."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1")]
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "stop-all"], input="n\n")
        assert result.exit_code != 0  # typer.Abort


# --- delete-all ---


def test_delete_all_no_pods():
    """delete-all with no pods prints message and exits 0."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = []
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "delete-all", "--confirm"])
        assert result.exit_code == 0
        assert "No pods to delete" in result.output


def test_delete_all_confirm_sequential():
    """delete-all --confirm deletes pods sequentially."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.delete_pod.return_value = {}
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "delete-all", "--confirm"])
        assert result.exit_code == 0
        assert mock_svc.delete_pod.call_count == 2


def test_delete_all_sequential_error():
    """delete-all sequential prints error for individual pod failures."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.delete_pod.side_effect = [None, RpctlError("fail")]
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "delete-all", "--confirm"])
        assert "Failed to delete" in result.output


def test_delete_all_parallel():
    """delete-all --parallel --confirm uses parallel_map."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        pods = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.list_pods.return_value = pods
        mock_svc_fn.return_value = mock_svc

        with patch("rpctl.services.parallel.parallel_map") as mock_parallel:
            mock_result = MagicMock()
            mock_result.succeeded = [({}, _make_pod("p1")), ({}, _make_pod("p2"))]
            mock_result.failed = []
            mock_parallel.return_value = mock_result

            result = runner.invoke(app, ["pod", "delete-all", "--confirm", "--parallel"])
            assert result.exit_code == 0
            mock_parallel.assert_called_once()


def test_delete_all_parallel_with_failures():
    """delete-all --parallel exits 1 when some pods fail."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        pods = [_make_pod("p1"), _make_pod("p2")]
        mock_svc.list_pods.return_value = pods
        mock_svc_fn.return_value = mock_svc

        with patch("rpctl.services.parallel.parallel_map") as mock_parallel:
            mock_result = MagicMock()
            mock_result.succeeded = [({}, _make_pod("p1"))]
            mock_result.failed = [(_make_pod("p2"), Exception("timeout"))]
            mock_parallel.return_value = mock_result

            result = runner.invoke(app, ["pod", "delete-all", "--confirm", "--parallel"])
            assert result.exit_code == 1


def test_delete_all_api_error():
    """delete-all exits 1 on API error during list."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.side_effect = RpctlError("API down")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "delete-all", "--confirm"])
        assert result.exit_code == 1


def test_delete_all_prompt_abort():
    """delete-all without --confirm prompts and aborts on 'n'."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.list_pods.return_value = [_make_pod("p1")]
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["pod", "delete-all"], input="n\n")
        assert result.exit_code != 0  # typer.Abort
