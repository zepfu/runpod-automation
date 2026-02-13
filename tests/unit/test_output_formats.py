"""Tests for CSV, YAML output and format routing."""

from __future__ import annotations

from unittest.mock import patch

from rpctl.models.pod import Pod
from rpctl.output.csv_output import _flatten, print_csv
from rpctl.output.formatter import output
from rpctl.output.yaml_output import print_yaml


def _pod():
    return Pod(
        id="pod-001",
        name="test-pod",
        status="RUNNING",
        gpu_type="A6000",
        gpu_count=1,
        image_name="nvidia/cuda",
        cost_per_hr=0.44,
    )


# --- CSV output ---


def test_csv_list(capsys):
    print_csv([_pod()])
    captured = capsys.readouterr()
    assert "id" in captured.out
    assert "pod-001" in captured.out


def test_csv_single(capsys):
    print_csv(_pod())
    captured = capsys.readouterr()
    assert "pod-001" in captured.out


def test_csv_dict(capsys):
    print_csv({"key": "value", "num": 42})
    captured = capsys.readouterr()
    assert "key" in captured.out
    assert "value" in captured.out


def test_csv_empty_list(capsys):
    print_csv([])
    captured = capsys.readouterr()
    assert captured.out == ""


def test_csv_string(capsys):
    print_csv("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_flatten_nested():
    result = _flatten({"a": {"b": 1, "c": 2}, "d": 3})
    assert result == {"a.b": 1, "a.c": 2, "d": 3}


def test_flatten_list():
    result = _flatten({"tags": ["a", "b", "c"]})
    assert result == {"tags": "a;b;c"}


# --- YAML output ---


def test_yaml_list(capsys):
    print_yaml([_pod()])
    captured = capsys.readouterr()
    assert "pod-001" in captured.out
    assert "name: test-pod" in captured.out


def test_yaml_single(capsys):
    print_yaml(_pod())
    captured = capsys.readouterr()
    assert "pod-001" in captured.out


def test_yaml_dict(capsys):
    print_yaml({"key": "value"})
    captured = capsys.readouterr()
    assert "key: value" in captured.out


def test_yaml_string(capsys):
    print_yaml("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.out


# --- Formatter routing ---


def test_output_format_json():
    with patch("rpctl.output.formatter.print_json") as mock:
        output({"a": 1}, output_format="json", table_type="pod_list")
        mock.assert_called_once()


def test_output_format_csv():
    with patch("rpctl.output.formatter.print_csv") as mock:
        output({"a": 1}, output_format="csv", table_type="pod_list")
        mock.assert_called_once()


def test_output_format_yaml():
    with patch("rpctl.output.formatter.print_yaml") as mock:
        output({"a": 1}, output_format="yaml", table_type="pod_list")
        mock.assert_called_once()


def test_output_format_table():
    """Table format uses the registered renderer."""
    from rpctl.output.tables import print_pod_list

    with patch.dict("rpctl.output.formatter.TABLE_RENDERERS", {"pod_list": print_pod_list}):
        # Just verify it doesn't crash — table renderer prints to console
        output([_pod()], output_format="table", table_type="pod_list")


def test_output_json_mode_backward_compat():
    """json_mode=True still works as shorthand."""
    with patch("rpctl.output.formatter.print_json") as mock:
        output({"a": 1}, json_mode=True, table_type="pod_list")
        mock.assert_called_once()


def test_output_format_overrides_json_mode():
    """Explicit output_format takes precedence over json_mode."""
    with patch("rpctl.output.formatter.print_csv") as mock:
        output({"a": 1}, json_mode=True, output_format="csv", table_type="pod_list")
        mock.assert_called_once()
