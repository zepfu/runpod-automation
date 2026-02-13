"""YAML output for --output yaml mode."""

from __future__ import annotations

import sys
from typing import Any

import yaml
from pydantic import BaseModel


def print_yaml(data: Any) -> None:
    """Print data as YAML to stdout."""
    serialized: Any
    if isinstance(data, list):
        serialized = [
            item.model_dump(exclude_none=True) if isinstance(item, BaseModel) else item
            for item in data
        ]
    elif isinstance(data, BaseModel):
        serialized = data.model_dump(exclude_none=True)
    elif isinstance(data, dict):
        serialized = data
    else:
        serialized = {"value": str(data)}
    yaml.dump(serialized, sys.stdout, default_flow_style=False, sort_keys=False)
