"""Tests for RestClient endpoint, registry, and user methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client():
    """Create a RestClient with a mocked runpod SDK."""
    with patch("rpctl.api.rest_client.runpod", create=True):
        from rpctl.api.rest_client import RestClient

        c = RestClient.__new__(RestClient)
        c._runpod = MagicMock()
        c._runpod.api_key = "test-key"
        return c


# --- Endpoint SDK-based methods ---


@patch("rpctl.api.retry.time.sleep")
def test_endpoint_health(mock_sleep, client):
    mock_ep = MagicMock()
    mock_ep.health.return_value = {"workers": {"idle": 1}}
    client._runpod.Endpoint.return_value = mock_ep

    result = client.endpoint_health("ep-1")
    assert result == {"workers": {"idle": 1}}
    client._runpod.Endpoint.assert_called_once_with("ep-1")


@patch("rpctl.api.retry.time.sleep")
def test_endpoint_run_sync(mock_sleep, client):
    mock_ep = MagicMock()
    mock_ep.run_sync.return_value = {"output": "done"}
    client._runpod.Endpoint.return_value = mock_ep

    result = client.endpoint_run_sync("ep-1", {"prompt": "hi"}, timeout=30)
    assert result == {"output": "done"}
    mock_ep.run_sync.assert_called_once_with({"prompt": "hi"}, 30)


@patch("rpctl.api.retry.time.sleep")
def test_endpoint_run_async(mock_sleep, client):
    mock_ep = MagicMock()
    mock_job = MagicMock()
    mock_job.job_id = "job-abc"
    mock_ep.run.return_value = mock_job
    client._runpod.Endpoint.return_value = mock_ep

    result = client.endpoint_run_async("ep-1", {"prompt": "hi"})
    assert result == "job-abc"
    mock_ep.run.assert_called_once_with({"prompt": "hi"})


@patch("rpctl.api.retry.time.sleep")
def test_endpoint_purge_queue(mock_sleep, client):
    mock_ep = MagicMock()
    mock_ep.purge_queue.return_value = {"removed": 5}
    client._runpod.Endpoint.return_value = mock_ep

    result = client.endpoint_purge_queue("ep-1")
    assert result == {"removed": 5}
    client._runpod.Endpoint.assert_called_once_with("ep-1")


# --- Endpoint HTTP-based methods ---


@patch("httpx.get")
def test_endpoint_job_status(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "COMPLETED", "output": "ok"}
    mock_get.return_value = mock_resp

    result = client.endpoint_job_status("ep-1", "job-1")
    assert result == {"status": "COMPLETED", "output": "ok"}
    mock_get.assert_called_once_with(
        "https://api.runpod.ai/v2/ep-1/status/job-1",
        headers={"Authorization": "Bearer test-key"},
    )
    mock_resp.raise_for_status.assert_called_once()


@patch("httpx.post")
def test_endpoint_job_cancel(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "CANCELLED"}
    mock_post.return_value = mock_resp

    result = client.endpoint_job_cancel("ep-1", "job-1")
    assert result == {"status": "CANCELLED"}
    mock_post.assert_called_once_with(
        "https://api.runpod.ai/v2/ep-1/cancel/job-1",
        headers={"Authorization": "Bearer test-key"},
    )
    mock_resp.raise_for_status.assert_called_once()


@patch("httpx.get")
def test_endpoint_stream(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"stream": [{"output": "chunk1"}, {"output": "chunk2"}]}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == [{"output": "chunk1"}, {"output": "chunk2"}]
    mock_get.assert_called_once_with(
        "https://api.runpod.ai/v2/ep-1/stream/job-1",
        headers={"Authorization": "Bearer test-key"},
    )


@patch("httpx.get")
def test_endpoint_stream_empty(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == []


# --- Registry auth methods ---


@patch("rpctl.api.retry.time.sleep")
def test_list_registry_auths(mock_sleep, client):
    client._runpod.get_user.return_value = {
        "containerRegistryAuths": [{"id": "ra-1", "name": "docker"}]
    }
    result = client.list_registry_auths()
    assert result == [{"id": "ra-1", "name": "docker"}]


@patch("rpctl.api.retry.time.sleep")
def test_list_registry_auths_none(mock_sleep, client):
    client._runpod.get_user.return_value = {"containerRegistryAuths": None}
    result = client.list_registry_auths()
    assert result == []


@patch("rpctl.api.retry.time.sleep")
def test_create_registry_auth(mock_sleep, client):
    client._runpod.create_container_registry_auth.return_value = {"id": "ra-1"}
    result = client.create_registry_auth("docker", "user", "pass")
    assert result == {"id": "ra-1"}
    client._runpod.create_container_registry_auth.assert_called_once_with("docker", "user", "pass")


@patch("rpctl.api.retry.time.sleep")
def test_update_registry_auth(mock_sleep, client):
    client._runpod.update_container_registry_auth.return_value = {"id": "ra-1"}
    result = client.update_registry_auth("ra-1", "newuser", "newpass")
    assert result == {"id": "ra-1"}
    client._runpod.update_container_registry_auth.assert_called_once_with(
        "ra-1", "newuser", "newpass"
    )


@patch("rpctl.api.retry.time.sleep")
def test_delete_registry_auth(mock_sleep, client):
    client._runpod.delete_container_registry_auth.return_value = {}
    result = client.delete_registry_auth("ra-1")
    assert result == {}
    client._runpod.delete_container_registry_auth.assert_called_once_with("ra-1")


# --- User methods ---


@patch("rpctl.api.retry.time.sleep")
def test_get_user(mock_sleep, client):
    client._runpod.get_user.return_value = {"id": "user-1", "email": "a@b.com"}
    result = client.get_user()
    assert result == {"id": "user-1", "email": "a@b.com"}


@patch("rpctl.api.retry.time.sleep")
def test_update_user_settings(mock_sleep, client):
    client._runpod.update_user_settings.return_value = {"id": "user-1"}
    result = client.update_user_settings("ssh-rsa AAAA")
    assert result == {"id": "user-1"}
    client._runpod.update_user_settings.assert_called_once_with("ssh-rsa AAAA")
