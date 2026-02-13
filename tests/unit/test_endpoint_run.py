"""Tests for endpoint run and purge-queue commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rpctl.errors import RpctlError

# --- EndpointService.run_sync() ---


def test_endpoint_service_run_sync():
    """run_sync() delegates to client.endpoint_run_sync()."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_run_sync.return_value = {"output": "hello", "status": "COMPLETED"}
    svc = EndpointService(mock_client)
    result = svc.run_sync("ep-123", {"prompt": "test"}, timeout=60)
    assert result["status"] == "COMPLETED"
    mock_client.endpoint_run_sync.assert_called_once_with("ep-123", {"prompt": "test"}, 60)


# --- EndpointService.run_async() ---


def test_endpoint_service_run_async():
    """run_async() delegates to client.endpoint_run_async(), returns job_id."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_run_async.return_value = "job-abc-123"
    svc = EndpointService(mock_client)
    job_id = svc.run_async("ep-123", {"prompt": "test"})
    assert job_id == "job-abc-123"
    mock_client.endpoint_run_async.assert_called_once_with("ep-123", {"prompt": "test"})


# --- EndpointService.purge_queue() ---


def test_endpoint_service_purge_queue():
    """purge_queue() delegates to client.endpoint_purge_queue()."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_purge_queue.return_value = {"status": "completed", "removed": 5}
    svc = EndpointService(mock_client)
    result = svc.purge_queue("ep-123")
    assert result["removed"] == 5
    mock_client.endpoint_purge_queue.assert_called_once_with("ep-123")


# --- CLI: rpctl endpoint run (sync) ---


def test_cli_endpoint_run_sync():
    """rpctl endpoint run EP_ID runs sync by default."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    mock_result = {"output": "hello world", "status": "COMPLETED"}

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.run_sync.return_value = mock_result
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "run", "ep-abc", "--input", '{"prompt": "hi"}'])
        assert result.exit_code == 0
        mock_svc.run_sync.assert_called_once_with("ep-abc", {"prompt": "hi"}, 86400)


# --- CLI: rpctl endpoint run (async) ---


def test_cli_endpoint_run_async():
    """rpctl endpoint run EP_ID --async submits async job."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.run_async.return_value = "job-xyz-789"
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app, ["endpoint", "run", "ep-abc", "--input", '{"prompt": "hi"}', "--async"]
        )
        assert result.exit_code == 0
        assert "job-xyz-789" in result.output
        mock_svc.run_async.assert_called_once_with("ep-abc", {"prompt": "hi"})


# --- CLI: rpctl endpoint run (invalid JSON) ---


def test_cli_endpoint_run_invalid_json():
    """rpctl endpoint run exits 1 on invalid JSON input."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()

    result = runner.invoke(app, ["endpoint", "run", "ep-abc", "--input", "not-valid-json"])
    assert result.exit_code == 1


# --- CLI: rpctl endpoint purge-queue ---


def test_cli_endpoint_purge_queue():
    """rpctl endpoint purge-queue EP_ID --confirm purges the queue."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()
    mock_result = {"status": "completed", "removed": 3}

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.purge_queue.return_value = mock_result
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "purge-queue", "ep-abc", "--confirm"])
        assert result.exit_code == 0
        mock_svc.purge_queue.assert_called_once_with("ep-abc")


# --- CLI: rpctl endpoint purge-queue (API error) ---


def test_cli_endpoint_purge_queue_api_error():
    """rpctl endpoint purge-queue exits 1 on API error."""
    from typer.testing import CliRunner

    from rpctl.main import app

    runner = CliRunner()

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.purge_queue.side_effect = RpctlError("API error")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "purge-queue", "ep-abc", "--confirm"])
        assert result.exit_code == 1
