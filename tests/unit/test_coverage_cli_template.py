"""Tests for remaining coverage gaps in rpctl.cli.template."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rpctl.main import app
from rpctl.models.template import Template

runner = CliRunner()


def _mock_template():
    return Template(
        id="tmpl-001",
        name="test-tmpl",
        image_name="pytorch:2.1",
        is_serverless=False,
    )


def test_create_with_docker_start_cmd():
    """template create passes --docker-start-cmd to service."""
    with patch("rpctl.cli.template._get_template_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_template.return_value = _mock_template()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "--name",
                "my-tmpl",
                "--image",
                "pytorch:2.1",
                "--docker-start-cmd",
                "python handler.py",
            ],
        )
        assert result.exit_code == 0
        call_kwargs = mock_svc.create_template.call_args[1]
        assert call_kwargs["docker_start_cmd"] == "python handler.py"


def test_create_with_volume_mount_path():
    """template create passes --volume-mount-path to service."""
    with patch("rpctl.cli.template._get_template_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_template.return_value = _mock_template()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "--name",
                "my-tmpl",
                "--image",
                "pytorch:2.1",
                "--volume-mount-path",
                "/workspace",
            ],
        )
        assert result.exit_code == 0
        call_kwargs = mock_svc.create_template.call_args[1]
        assert call_kwargs["volume_mount_path"] == "/workspace"


def test_create_with_registry_auth():
    """template create passes --registry-auth to service."""
    with patch("rpctl.cli.template._get_template_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_template.return_value = _mock_template()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "--name",
                "my-tmpl",
                "--image",
                "private/image:latest",
                "--registry-auth",
                "reg-001",
            ],
        )
        assert result.exit_code == 0
        call_kwargs = mock_svc.create_template.call_args[1]
        assert call_kwargs["registry_auth_id"] == "reg-001"


def test_create_with_all_extra_options():
    """template create with all three extra options at once."""
    with patch("rpctl.cli.template._get_template_service") as mock_svc_fn:
        mock_svc = MagicMock()
        mock_svc.create_template.return_value = _mock_template()
        mock_svc_fn.return_value = mock_svc

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "--name",
                "full-tmpl",
                "--image",
                "private/image:latest",
                "--docker-start-cmd",
                "bash start.sh",
                "--volume-mount-path",
                "/data",
                "--registry-auth",
                "reg-002",
            ],
        )
        assert result.exit_code == 0
        call_kwargs = mock_svc.create_template.call_args[1]
        assert call_kwargs["docker_start_cmd"] == "bash start.sh"
        assert call_kwargs["volume_mount_path"] == "/data"
        assert call_kwargs["registry_auth_id"] == "reg-002"
