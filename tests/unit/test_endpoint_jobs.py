"""Tests for endpoint job-status and job-cancel commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rpctl.errors import ApiError
from rpctl.services.endpoint_service import EndpointService
from typer.testing import CliRunner

runner = CliRunner()


# --- Service tests ---


class TestEndpointServiceJobs:
    def test_job_status(self) -> None:
        client = MagicMock()
        client.endpoint_job_status.return_value = {
            "id": "job-123",
            "status": "COMPLETED",
            "output": {"result": "ok"},
        }
        svc = EndpointService(client)
        result = svc.job_status("ep-abc", "job-123")
        assert result["status"] == "COMPLETED"
        client.endpoint_job_status.assert_called_once_with("ep-abc", "job-123")

    def test_job_cancel(self) -> None:
        client = MagicMock()
        client.endpoint_job_cancel.return_value = {
            "id": "job-123",
            "status": "CANCELLED",
        }
        svc = EndpointService(client)
        result = svc.job_cancel("ep-abc", "job-123")
        assert result["status"] == "CANCELLED"
        client.endpoint_job_cancel.assert_called_once_with("ep-abc", "job-123")


# --- CLI tests ---


class TestEndpointJobsCLI:
    @patch("rpctl.cli.endpoint._get_endpoint_service")
    def test_job_status_table(self, mock_svc_fn: MagicMock) -> None:
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.job_status.return_value = {
            "id": "job-123",
            "status": "COMPLETED",
        }
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["endpoint", "job-status", "ep-abc", "job-123"],
        )
        assert result.exit_code == 0

    @patch("rpctl.cli.endpoint._get_endpoint_service")
    def test_job_status_json(self, mock_svc_fn: MagicMock) -> None:
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.job_status.return_value = {
            "id": "job-123",
            "status": "IN_PROGRESS",
        }
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            [
                "--output",
                "json",
                "endpoint",
                "job-status",
                "ep-abc",
                "job-123",
            ],
        )
        assert result.exit_code == 0

    @patch("rpctl.cli.endpoint._get_endpoint_service")
    def test_job_cancel_success(self, mock_svc_fn: MagicMock) -> None:
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.job_cancel.return_value = {
            "id": "job-123",
            "status": "CANCELLED",
        }
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["endpoint", "job-cancel", "ep-abc", "job-123"],
        )
        assert result.exit_code == 0

    @patch("rpctl.cli.endpoint._get_endpoint_service")
    def test_job_status_error(self, mock_svc_fn: MagicMock) -> None:
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.job_status.side_effect = ApiError("Not found")
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["endpoint", "job-status", "ep-abc", "job-123"],
        )
        assert result.exit_code != 0

    @patch("rpctl.cli.endpoint._get_endpoint_service")
    def test_job_cancel_error(self, mock_svc_fn: MagicMock) -> None:
        from rpctl.main import app

        mock_svc = MagicMock()
        mock_svc.job_cancel.side_effect = ApiError("Failed")
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["endpoint", "job-cancel", "ep-abc", "job-123"],
        )
        assert result.exit_code != 0
