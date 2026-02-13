"""JSON output for --json mode."""

from __future__ import annotations

import json
from typing import Any

import typer
from pydantic import BaseModel


def print_json(data: Any) -> None:
    """Print data as formatted JSON to stdout."""
    serialized = [_serialize(item) for item in data] if isinstance(data, list) else _serialize(data)
    typer.echo(json.dumps(serialized, indent=2, default=str))


def _serialize(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(exclude_none=True)
    if isinstance(obj, dict):
        return obj
    return str(obj)
