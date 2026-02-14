"""Tests for endpoint stream command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.main import app

runner = CliRunner()


def test_cli_endpoint_stream_success():
    """rpctl endpoint stream EP_ID JOB_ID succeeds."""
    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.stream.return_value = [
            {"output": "chunk1"},
            {"output": "chunk2"},
        ]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["endpoint", "stream", "ep-123", "job-456"])
        assert result.exit_code == 0
        mock_svc.stream.assert_called_once_with("ep-123", "job-456")


def test_cli_endpoint_stream_empty():
    """rpctl endpoint stream with no output."""
    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.stream.return_value = []
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["endpoint", "stream", "ep-123", "job-456"])
        assert result.exit_code == 0


def test_cli_endpoint_stream_json():
    """rpctl --json endpoint stream outputs JSON."""
    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.stream.return_value = [{"output": "data"}]
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["--json", "endpoint", "stream", "ep-123", "job-456"],
        )
        assert result.exit_code == 0


def test_cli_endpoint_stream_error():
    """rpctl endpoint stream handles API errors."""
    from rpctl.errors import RpctlError

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.stream.side_effect = RpctlError("Stream failed")
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(app, ["endpoint", "stream", "ep-123", "job-456"])
        assert result.exit_code == 1


def test_service_stream():
    """EndpointService.stream() delegates to client."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_stream.return_value = [{"output": "test"}]
    svc = EndpointService(mock_client)
    result = svc.stream("ep-123", "job-456")
    assert result == [{"output": "test"}]
    mock_client.endpoint_stream.assert_called_once_with("ep-123", "job-456")


def test_table_renderer_stream_chunks():
    """print_endpoint_stream renders chunks."""
    from rpctl.output.tables import print_endpoint_stream

    # Should not raise
    print_endpoint_stream([{"output": "hello"}, {"output": "world"}])


def test_table_renderer_stream_empty():
    """print_endpoint_stream handles empty list."""
    from rpctl.output.tables import print_endpoint_stream

    print_endpoint_stream([])
