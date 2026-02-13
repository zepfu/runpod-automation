"""Tests for endpoint health and wait commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rpctl.errors import RpctlError
from rpctl.services.poll import PollTimeoutError

# --- EndpointService.health() ---


def test_endpoint_service_health():
    """health() delegates to client.endpoint_health()."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_health.return_value = {
        "workers": {"ready": 2, "idle": 1, "running": 1},
        "jobs": {"completed": 100, "failed": 5},
    }
    svc = EndpointService(mock_client)
    result = svc.health("ep-123")
    assert result["workers"]["ready"] == 2
    mock_client.endpoint_health.assert_called_once_with("ep-123")


# --- EndpointService.wait_until_ready() ---


def test_endpoint_service_wait_until_ready():
    """wait_until_ready returns when workers are ready."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    # First call: no workers, second call: workers ready
    mock_client.endpoint_health.side_effect = [
        {"workers": {"ready": 0, "idle": 0}, "jobs": {}},
        {"workers": {"ready": 1, "idle": 0}, "jobs": {}},
    ]
    svc = EndpointService(mock_client)
    result = svc.wait_until_ready("ep-123", timeout=10, interval=0.01)
    assert result["workers"]["ready"] == 1
    assert mock_client.endpoint_health.call_count == 2


def test_endpoint_service_wait_timeout():
    """wait_until_ready raises PollTimeoutError on timeout."""
    from rpctl.services.endpoint_service import EndpointService

    mock_client = MagicMock()
    mock_client.endpoint_health.return_value = {
        "workers": {"ready": 0, "idle": 0},
        "jobs": {},
    }
    svc = EndpointService(mock_client)
    with pytest.raises(PollTimeoutError):
        svc.wait_until_ready("ep-123", timeout=0.05, interval=0.01)


# --- CLI: rpctl endpoint health ---


def test_cli_endpoint_health():
    """rpctl endpoint health EP_ID returns health data."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    mock_health = {
        "workers": {"ready": 2, "idle": 1},
        "jobs": {"completed": 50},
    }

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.health.return_value = mock_health
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "health", "ep-abc"])
        assert result.exit_code == 0
        mock_svc.health.assert_called_once_with("ep-abc")


def test_cli_endpoint_health_json():
    """rpctl endpoint health EP_ID --output json outputs JSON."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    mock_health = {
        "workers": {"ready": 1, "idle": 0},
        "jobs": {"completed": 10},
    }

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.health.return_value = mock_health
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["--output", "json", "endpoint", "health", "ep-abc"])
        assert result.exit_code == 0
        assert "ready" in result.output


def test_cli_endpoint_health_api_error():
    """rpctl endpoint health handles API errors."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.health.side_effect = RpctlError("Not found")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "health", "ep-bad"])
        assert result.exit_code == 1


# --- CLI: rpctl endpoint wait ---


def test_cli_endpoint_wait_success():
    """rpctl endpoint wait EP_ID succeeds when workers ready."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()
    mock_health = {
        "workers": {"ready": 1, "idle": 0},
        "jobs": {},
    }

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_ready.return_value = mock_health
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app, ["endpoint", "wait", "ep-abc", "--timeout", "60", "--interval", "1"]
        )
        assert result.exit_code == 0
        mock_svc.wait_until_ready.assert_called_once_with("ep-abc", timeout=60, interval=1)


def test_cli_endpoint_wait_timeout():
    """rpctl endpoint wait exits 2 on timeout."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_ready.side_effect = PollTimeoutError("timed out")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "wait", "ep-abc"])
        assert result.exit_code == 2


def test_cli_endpoint_wait_api_error():
    """rpctl endpoint wait exits 1 on API error."""
    from rpctl.main import app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.wait_until_ready.side_effect = RpctlError("API error")
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(app, ["endpoint", "wait", "ep-abc"])
        assert result.exit_code == 1
