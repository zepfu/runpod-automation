"""Tests for RestClient endpoint, registry, and user methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client():
    """Create a RestClient with a mocked GraphQL client."""
    from rpctl.api.rest_client import RestClient

    c = RestClient.__new__(RestClient)
    c._api_key = "test-key"
    c._gql = MagicMock()
    return c


# --- Endpoint REST-based methods ---


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_health(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"workers": {"idle": 1}}
    mock_get.return_value = mock_resp

    result = client.endpoint_health("ep-1")
    assert result == {"workers": {"idle": 1}}
    mock_get.assert_called_once()


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_run_sync(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"output": "done"}
    mock_post.return_value = mock_resp

    result = client.endpoint_run_sync("ep-1", {"prompt": "hi"}, timeout=30)
    assert result == {"output": "done"}
    mock_post.assert_called_once()


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_run_async(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "job-abc"}
    mock_post.return_value = mock_resp

    result = client.endpoint_run_async("ep-1", {"prompt": "hi"})
    assert result == "job-abc"


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_purge_queue(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"removed": 5}
    mock_post.return_value = mock_resp

    result = client.endpoint_purge_queue("ep-1")
    assert result == {"removed": 5}


# --- Endpoint HTTP-based methods ---


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_job_status(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "COMPLETED", "output": "ok"}
    mock_get.return_value = mock_resp

    result = client.endpoint_job_status("ep-1", "job-1")
    assert result == {"status": "COMPLETED", "output": "ok"}
    mock_get.assert_called_once()


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_job_cancel(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "CANCELLED"}
    mock_post.return_value = mock_resp

    result = client.endpoint_job_cancel("ep-1", "job-1")
    assert result == {"status": "CANCELLED"}
    mock_post.assert_called_once()


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_stream(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"stream": [{"output": "chunk1"}, {"output": "chunk2"}]}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == [{"output": "chunk1"}, {"output": "chunk2"}]
    mock_get.assert_called_once()


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_stream_empty(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == []


# --- Registry auth methods ---


def test_list_registry_auths(client):
    client._gql.execute.return_value = {
        "myself": {"containerRegistryAuths": [{"id": "ra-1", "name": "docker"}]}
    }
    result = client.list_registry_auths()
    assert result == [{"id": "ra-1", "name": "docker"}]


def test_list_registry_auths_empty(client):
    client._gql.execute.return_value = {"myself": {"containerRegistryAuths": []}}
    result = client.list_registry_auths()
    assert result == []


def test_create_registry_auth(client):
    client._gql.execute.return_value = {"saveRegistryAuth": {"id": "ra-1"}}
    result = client.create_registry_auth("docker", "user", "pass")
    assert result == {"id": "ra-1"}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveRegistryAuth" in call_args


def test_update_registry_auth(client):
    client._gql.execute.return_value = {"updateRegistryAuth": {"id": "ra-1"}}
    result = client.update_registry_auth("ra-1", "newuser", "newpass")
    assert result == {"id": "ra-1"}
    call_args = client._gql.execute.call_args[0][0]
    assert "updateRegistryAuth" in call_args


def test_delete_registry_auth(client):
    client._gql.execute.return_value = {"deleteRegistryAuth": None}
    result = client.delete_registry_auth("ra-1")
    assert result == {"deleteRegistryAuth": None}
    call_args = client._gql.execute.call_args[0][0]
    assert "deleteRegistryAuth" in call_args


# --- User methods ---


def test_get_user(client):
    client._gql.execute.return_value = {"myself": {"id": "user-1", "pubKey": "ssh-rsa"}}
    result = client.get_user()
    assert result == {"id": "user-1", "pubKey": "ssh-rsa"}


def test_update_user_settings(client):
    client._gql.execute.return_value = {"updateUserSettings": {"id": "user-1"}}
    result = client.update_user_settings("ssh-rsa AAAA")
    assert result == {"id": "user-1"}
    call_args = client._gql.execute.call_args[0][0]
    assert "updateUserSettings" in call_args
