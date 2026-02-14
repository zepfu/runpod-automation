"""Tests for remaining coverage gaps in rpctl.output.tables."""

from __future__ import annotations

from unittest.mock import MagicMock

from rpctl.output.tables import (
    print_endpoint_health,
    print_endpoint_job_status,
    print_endpoint_purge_result,
    print_endpoint_run_result,
    print_registry_detail,
    print_user_info,
)

# --- print_endpoint_health ---


def test_endpoint_health_with_top_level_fields():
    """Health dict with requestsPerMinute, avgResponseTime, queueLength."""
    health = {
        "workers": {"ready": 2, "idle": 1},
        "jobs": {"completed": 100, "failed": 5},
        "requestsPerMinute": 42,
        "avgResponseTime": 120.5,
        "queueLength": 7,
    }
    # Should not raise
    print_endpoint_health(health)


def test_endpoint_health_non_dict():
    """Health with a non-dict input falls back to _detail_table."""
    mock_obj = MagicMock()
    mock_obj.model_dump.return_value = {"status": "healthy"}
    print_endpoint_health(mock_obj)


# --- print_endpoint_run_result ---


def test_endpoint_run_result_non_dict():
    """Run result with non-dict input prints directly."""
    print_endpoint_run_result("some string result")


def test_endpoint_run_result_dict():
    """Run result with dict input renders a table."""
    print_endpoint_run_result({"id": "run-123", "status": "IN_QUEUE"})


# --- print_endpoint_job_status ---


def test_endpoint_job_status_output_dict_truncation():
    """Job status with output as a dict truncates to 200 chars."""
    result = {
        "id": "job-123",
        "status": "COMPLETED",
        "output": {"data": "x" * 300},
    }
    # Should not raise
    print_endpoint_job_status(result)


def test_endpoint_job_status_non_dict():
    """Job status with non-dict input prints directly."""
    print_endpoint_job_status("job status string")


def test_endpoint_job_status_dict_no_output():
    """Job status dict without output key."""
    print_endpoint_job_status({"id": "job-1", "status": "IN_QUEUE"})


# --- print_endpoint_purge_result ---


def test_endpoint_purge_result_non_dict():
    """Purge result with non-dict input prints 'Queue purged.'."""
    print_endpoint_purge_result("done")


def test_endpoint_purge_result_dict():
    """Purge result with dict input renders a table."""
    print_endpoint_purge_result({"removed": 5, "status": "completed"})


# --- print_user_info ---


def test_user_info_with_ssh_key_and_volumes():
    """User info with SSH key present and network volumes."""
    data = {
        "id": "user-123",
        "pubKey": "ssh-ed25519 AAAA" + "B" * 40,
        "networkVolumes": [
            {"id": "vol-1", "name": "my-vol", "size": 100},
            {"id": "vol-2", "name": "data-vol", "size": 200},
        ],
    }
    # Should not raise
    print_user_info(data)


def test_user_info_with_short_ssh_key():
    """User info with a short SSH key (no truncation needed)."""
    data = {
        "id": "user-456",
        "pubKey": "ssh-ed25519 short",
        "networkVolumes": [],
    }
    print_user_info(data)


def test_user_info_non_dict():
    """User info with non-dict input prints directly."""
    print_user_info("raw user data")


def test_user_info_no_pub_key():
    """User info with empty pubKey shows 'Not set'."""
    data = {
        "id": "user-789",
        "pubKey": "",
        "networkVolumes": [],
    }
    print_user_info(data)


def test_user_info_volumes_with_missing_name():
    """User info with volumes that have no name falls back to id."""
    data = {
        "id": "user-100",
        "pubKey": "ssh-rsa AAAA",
        "networkVolumes": [
            {"id": "vol-x", "size": 50},
        ],
    }
    print_user_info(data)


# --- print_registry_detail ---


def test_registry_detail_non_dict():
    """Registry detail with non-dict input prints directly."""
    print_registry_detail("raw registry data")


def test_registry_detail_dict():
    """Registry detail with dict input renders a table (no password)."""
    print_registry_detail({"id": "reg-001", "name": "docker-hub", "password": "secret"})
