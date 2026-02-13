"""Integration tests for main CLI."""

from __future__ import annotations

from rpctl.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "rpctl" in result.output
    assert "config" in result.output
    assert "capacity" in result.output


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "rpctl 0.1.0" in result.output


def test_no_args_shows_help():
    result = runner.invoke(app, [])
    # Typer's no_args_is_help exits with code 0 or 2 depending on version
    assert result.exit_code in (0, 2)
    assert "config" in result.output
