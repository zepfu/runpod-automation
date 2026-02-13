"""CSV output for --output csv mode."""

from __future__ import annotations

import csv
import sys
from typing import Any

from pydantic import BaseModel


def print_csv(data: Any, *, table_type: str = "") -> None:
    """Print data as CSV to stdout."""
    if isinstance(data, BaseModel):
        rows = [data.model_dump(exclude_none=True)]
    elif isinstance(data, list):
        rows = [
            item.model_dump(exclude_none=True) if isinstance(item, BaseModel) else item
            for item in data
        ]
    elif isinstance(data, dict):
        rows = [data]
    else:
        rows = [{"value": str(data)}]

    if not rows:
        return

    flat_rows = [_flatten(r) if isinstance(r, dict) else {"value": str(r)} for r in rows]
    fieldnames = list(flat_rows[0].keys())

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(flat_rows)


def _flatten(d: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten nested dicts for CSV output."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        elif isinstance(v, list):
            items.append((new_key, ";".join(str(i) for i in v)))
        else:
            items.append((new_key, v))
    return dict(items)
