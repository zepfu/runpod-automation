"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def gpu_types_response():
    """Sample GraphQL gpuTypes response."""
    return json.loads((FIXTURES / "gpu_types.json").read_text())


@pytest.fixture
def datacenter_response():
    """Sample GraphQL datacenter availability response."""
    return json.loads((FIXTURES / "datacenters.json").read_text())


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config directory and file."""
    config_dir = tmp_path / "rpctl"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "version: 1\n"
        "active_profile: default\n"
        "defaults:\n"
        "  cloud_type: secure\n"
        "  output_format: table\n"
        "profiles:\n"
        "  default:\n"
        "    cloud_type: secure\n"
        "  work:\n"
        "    cloud_type: community\n"
    )
    return config_file
