"""Tests for --dry-run flag on create commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.main import app

runner = CliRunner()


def test_pod_create_dry_run():
    """rpctl pod create --dry-run shows params without creating."""
    result = runner.invoke(
        app,
        [
            "pod",
            "create",
            "--image",
            "nvidia/cuda",
            "--gpu",
            "A100",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    # Should NOT call any API
    assert "nvidia/cuda" in result.output or "Dry Run" in result.output


def test_pod_create_dry_run_json():
    """rpctl --json pod create --dry-run outputs JSON."""
    result = runner.invoke(
        app,
        [
            "--json",
            "pod",
            "create",
            "--image",
            "test",
            "--gpu",
            "A100",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    import json

    parsed = json.loads(result.output)
    assert parsed["image_name"] == "test"


def test_template_create_dry_run():
    """rpctl template create --dry-run shows params without creating."""
    result = runner.invoke(
        app,
        [
            "template",
            "create",
            "--name",
            "test-tmpl",
            "--image",
            "python:3.12",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "test-tmpl" in result.output or "Dry Run" in result.output


def test_template_create_dry_run_json():
    """rpctl --json template create --dry-run outputs JSON."""
    result = runner.invoke(
        app,
        [
            "--json",
            "template",
            "create",
            "--name",
            "test-tmpl",
            "--image",
            "python:3.12",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    import json

    parsed = json.loads(result.output)
    assert parsed["name"] == "test-tmpl"


def test_pod_create_without_dry_run_calls_api():
    """Without --dry-run, pod create calls the API."""
    with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
        mock_svc = MagicMock()
        from rpctl.models.pod import Pod

        mock_svc.create_pod.return_value = Pod(
            id="pod-123",
            name="test",
            status="RUNNING",
            gpu_type="A100",
            gpu_count=1,
            image_name="test",
        )
        mock_svc_fn.return_value = mock_svc
        result = runner.invoke(
            app,
            ["pod", "create", "--image", "test", "--gpu", "A100"],
        )
        assert result.exit_code == 0
        mock_svc.create_pod.assert_called_once()
