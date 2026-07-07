"""Unit tests for RestClient (GraphQL-based)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError


@pytest.fixture
def client():
    """Create a RestClient with a mocked GraphQL client."""
    from rpctl.api.rest_client import RestClient

    c = RestClient.__new__(RestClient)
    c._api_key = "test-key"
    c._gql = MagicMock()
    return c


# --- RestClient __init__ ---


def test_init_creates_graphql_client():
    """__init__ creates GraphQLClient and stores api_key."""
    with patch("rpctl.api.graphql_client.GraphQLClient") as mock_gql:
        from rpctl.api.rest_client import RestClient

        c = RestClient("my-api-key")
        assert c._api_key == "my-api-key"
        mock_gql.assert_called_once_with("my-api-key")
        assert c._gql is mock_gql.return_value


# --- Pod tests ---


def test_get_pods(client):
    client._gql.execute.return_value = {"myself": {"pods": [{"id": "p1"}]}}
    result = client.get_pods()
    assert result == [{"id": "p1"}]
    client._gql.execute.assert_called_once()


def test_get_pods_empty(client):
    client._gql.execute.return_value = {"myself": {"pods": []}}
    result = client.get_pods()
    assert result == []


def test_get_pod_success(client):
    client._gql.execute.return_value = {"pod": {"id": "p1"}}
    result = client.get_pod("p1")
    assert result == {"id": "p1"}


def test_get_pod_not_found_empty(client):
    """get_pod with None result raises ResourceNotFoundError."""
    client._gql.execute.return_value = {"pod": None}
    with pytest.raises(ResourceNotFoundError, match="Pod 'xyz' not found"):
        client.get_pod("xyz")


def test_create_pod(client):
    client._gql.execute.return_value = {"podFindAndDeployOnDemand": {"id": "p1"}}
    result = client.create_pod(name="test", image_name="img")
    assert result == {"id": "p1"}


def test_create_pod_cpu(client):
    """CPU pod creation returns deployCpuPod result."""
    client._gql.execute.return_value = {"deployCpuPod": {"id": "cpu-1"}}
    result = client.create_pod(name="test", image_name="img")
    assert result == {"id": "cpu-1"}


def test_create_pod_empty_response(client):
    """create_pod returns empty dict if neither key present."""
    client._gql.execute.return_value = {}
    result = client.create_pod(name="test", image_name="img")
    assert result == {}


def test_stop_pod(client):
    client._gql.execute.return_value = {"podStop": {"id": "p1", "desiredStatus": "EXITED"}}
    result = client.stop_pod("p1")
    assert result == {"id": "p1", "desiredStatus": "EXITED"}


def test_resume_pod(client):
    client._gql.execute.return_value = {"podResume": {"id": "p1", "desiredStatus": "RUNNING"}}
    result = client.resume_pod("p1")
    assert result == {"id": "p1", "desiredStatus": "RUNNING"}


def test_resume_pod_with_gpu_count(client):
    """resume_pod passes gpu_count kwarg."""
    client._gql.execute.return_value = {"podResume": {"id": "p1"}}
    client.resume_pod("p1", gpu_count=2)
    call_args = client._gql.execute.call_args[0][0]
    assert "gpuCount: 2" in call_args


def test_terminate_pod(client):
    client._gql.execute.return_value = {"podTerminate": None}
    result = client.terminate_pod("p1")
    assert result == {"podTerminate": None}


# --- Endpoint tests ---


def test_get_endpoints(client):
    """get_endpoints uses GraphQL query."""
    client._gql.execute.return_value = {
        "myself": {"endpoints": [{"id": "ep1"}]},
    }
    result = client.get_endpoints()
    assert result == [{"id": "ep1"}]
    client._gql.execute.assert_called_once()


def test_get_endpoint_success(client):
    """get_endpoint filters from list by ID."""
    client._gql.execute.return_value = {
        "myself": {"endpoints": [{"id": "ep1"}, {"id": "ep2"}]},
    }
    result = client.get_endpoint("ep1")
    assert result == {"id": "ep1"}


def test_get_endpoint_not_found_empty(client):
    """get_endpoint with no matching ID raises ResourceNotFoundError."""
    client._gql.execute.return_value = {"myself": {"endpoints": []}}
    with pytest.raises(ResourceNotFoundError, match="Endpoint 'ep-1' not found"):
        client.get_endpoint("ep-1")


def test_create_endpoint(client):
    """create_endpoint uses saveEndpoint GraphQL mutation."""
    client._gql.execute.return_value = {"saveEndpoint": {"id": "ep1", "name": "test"}}
    result = client.create_endpoint(name="test", templateId="t1")
    assert result == {"id": "ep1", "name": "test"}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveEndpoint" in call_args


def test_update_endpoint(client):
    """update_endpoint uses saveEndpoint GraphQL mutation with id."""
    client._gql.execute.return_value = {
        "saveEndpoint": {"id": "ep1", "workersMax": 10},
    }
    result = client.update_endpoint("ep1", workersMax=10)
    assert result == {"id": "ep1", "workersMax": 10}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveEndpoint" in call_args
    assert '"ep1"' in call_args


def test_delete_endpoint(client):
    """delete_endpoint uses deleteEndpoint GraphQL mutation."""
    client._gql.execute.return_value = {"deleteEndpoint": None}
    result = client.delete_endpoint("ep1")
    assert result == {"deleteEndpoint": None}
    call_args = client._gql.execute.call_args[0][0]
    assert "deleteEndpoint" in call_args


# --- Template tests ---


def test_get_templates(client):
    """get_templates uses GraphQL query."""
    client._gql.execute.return_value = {"podTemplates": [{"id": "t1"}]}
    result = client.get_templates()
    assert result == [{"id": "t1"}]


def test_get_template_success(client):
    """get_template uses GraphQL query by ID."""
    client._gql.execute.return_value = {"podTemplate": {"id": "t1", "name": "test"}}
    result = client.get_template("t1")
    assert result == {"id": "t1", "name": "test"}


def test_get_template_not_found_empty(client):
    """get_template with falsy return raises ResourceNotFoundError."""
    client._gql.execute.return_value = {"podTemplate": None}
    with pytest.raises(ResourceNotFoundError, match="Template 'tmpl-1' not found"):
        client.get_template("tmpl-1")


def test_create_template(client):
    """create_template uses saveTemplate GraphQL mutation."""
    client._gql.execute.return_value = {"saveTemplate": {"id": "t1", "name": "test"}}
    result = client.create_template(name="test", imageName="img")
    assert result == {"id": "t1", "name": "test"}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveTemplate" in call_args


def test_update_template(client):
    """update_template uses saveTemplate GraphQL mutation with id."""
    client._gql.execute.return_value = {
        "saveTemplate": {"id": "t1", "name": "updated"},
    }
    result = client.update_template("t1", name="updated")
    assert result == {"id": "t1", "name": "updated"}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveTemplate" in call_args


def test_delete_template(client):
    """delete_template fetches name first, then deletes by name."""
    # First call: get_template to find the name
    # Second call: deleteTemplate mutation
    client._gql.execute.side_effect = [
        {"podTemplate": {"id": "t1", "name": "my-template"}},
        {"deleteTemplate": None},
    ]
    result = client.delete_template("t1")
    assert result == {"deleteTemplate": None}
    assert client._gql.execute.call_count == 2
    delete_call = client._gql.execute.call_args[0][0]
    assert "deleteTemplate" in delete_call
    assert "my-template" in delete_call


# --- Volume tests ---


def test_get_volumes(client):
    """get_volumes uses GraphQL query."""
    client._gql.execute.return_value = {
        "myself": {"networkVolumes": [{"id": "v1"}]},
    }
    result = client.get_volumes()
    assert result == [{"id": "v1"}]


def test_get_volume_success(client):
    """get_volume filters from list by ID."""
    client._gql.execute.return_value = {
        "myself": {"networkVolumes": [{"id": "v1"}, {"id": "v2"}]},
    }
    result = client.get_volume("v1")
    assert result == {"id": "v1"}


def test_get_volume_not_found_empty(client):
    """get_volume with no matching ID raises ResourceNotFoundError."""
    client._gql.execute.return_value = {"myself": {"networkVolumes": []}}
    with pytest.raises(ResourceNotFoundError, match="Volume 'vol-1' not found"):
        client.get_volume("vol-1")


def test_create_volume(client):
    """create_volume uses GraphQL mutation."""
    client._gql.execute.return_value = {
        "createNetworkVolume": {"id": "v1", "name": "test", "size": 100},
    }
    result = client.create_volume(name="test", size=100, data_center_id="US-TX-3")
    assert result == {"id": "v1", "name": "test", "size": 100}
    call_args = client._gql.execute.call_args[0][0]
    assert "createNetworkVolume" in call_args


def test_update_volume(client):
    """update_volume uses GraphQL mutation."""
    client._gql.execute.return_value = {
        "updateNetworkVolume": {"id": "v1", "name": "updated"},
    }
    result = client.update_volume("v1", name="updated")
    assert result == {"id": "v1", "name": "updated"}
    call_args = client._gql.execute.call_args[0][0]
    assert "updateNetworkVolume" in call_args


def test_delete_volume(client):
    """delete_volume uses GraphQL mutation."""
    client._gql.execute.return_value = {"deleteNetworkVolume": None}
    result = client.delete_volume("v1")
    assert result == {"deleteNetworkVolume": None}
    call_args = client._gql.execute.call_args[0][0]
    assert "deleteNetworkVolume" in call_args


# --- GPU tests ---


def test_get_gpus(client):
    client._gql.execute.return_value = {"gpuTypes": [{"id": "A100"}]}
    result = client.get_gpus()
    assert result == [{"id": "A100"}]


def test_get_gpus_empty(client):
    client._gql.execute.return_value = {"gpuTypes": []}
    result = client.get_gpus()
    assert result == []


def test_get_gpu(client):
    client._gql.execute.return_value = {"gpuTypes": [{"id": "A100", "displayName": "A100"}]}
    result = client.get_gpu("A100")
    assert result == {"id": "A100", "displayName": "A100"}


def test_get_gpu_not_found(client):
    """get_gpu with empty types returns empty dict."""
    client._gql.execute.return_value = {"gpuTypes": []}
    result = client.get_gpu("NONEXISTENT")
    assert result == {}


# --- Endpoint REST helper tests ---


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_get(mock_get, client):
    """_endpoint_rest GET makes correct httpx call."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_resp

    result = client._endpoint_rest("GET", "ep-1/health", timeout=3)
    assert result == {"status": "ok"}
    mock_get.assert_called_once_with(
        "https://api.runpod.ai/v2/ep-1/health",
        headers={
            "Authorization": "Bearer test-key",
            "Content-Type": "application/json",
        },
        timeout=3,
    )


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_rest_post(mock_post, client):
    """_endpoint_rest POST makes correct httpx call."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "job-1"}
    mock_post.return_value = mock_resp

    result = client._endpoint_rest("POST", "ep-1/run", json={"input": {"prompt": "hi"}})
    assert result == {"id": "job-1"}


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_auth_error(mock_get, client):
    """_endpoint_rest raises AuthenticationError on 401."""
    resp = httpx.Response(401, request=httpx.Request("GET", "http://test"))
    mock_get.side_effect = httpx.HTTPStatusError("", request=resp.request, response=resp)

    with pytest.raises(AuthenticationError, match="Invalid API key"):
        client._endpoint_rest("GET", "ep-1/health")


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_not_found(mock_get, client):
    """_endpoint_rest raises ResourceNotFoundError on 404."""
    resp = httpx.Response(404, request=httpx.Request("GET", "http://test"))
    mock_get.side_effect = httpx.HTTPStatusError("", request=resp.request, response=resp)

    with pytest.raises(ResourceNotFoundError, match="Not found"):
        client._endpoint_rest("GET", "ep-1/health")


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_server_error(mock_get, client):
    """_endpoint_rest raises ApiError on 500."""
    resp = httpx.Response(500, request=httpx.Request("GET", "http://test"))
    mock_get.side_effect = httpx.HTTPStatusError("", request=resp.request, response=resp)

    with pytest.raises(ApiError, match="Endpoint API error: 500"):
        client._endpoint_rest("GET", "ep-1/health")


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_connect_error(mock_get, client):
    """_endpoint_rest raises ApiError on connection failure."""
    mock_get.side_effect = httpx.ConnectError("Connection refused")

    with pytest.raises(ApiError, match="Cannot connect"):
        client._endpoint_rest("GET", "ep-1/health")


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_rest_timeout(mock_get, client):
    """_endpoint_rest raises ApiError on timeout."""
    mock_get.side_effect = httpx.TimeoutException("Timed out")

    with pytest.raises(ApiError, match="Request timed out"):
        client._endpoint_rest("GET", "ep-1/health")


# --- Endpoint high-level method tests ---


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_health(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"workers": {"idle": 1}}
    mock_get.return_value = mock_resp

    result = client.endpoint_health("ep-1")
    assert result == {"workers": {"idle": 1}}


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_run_sync(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"output": "done"}
    mock_post.return_value = mock_resp

    result = client.endpoint_run_sync("ep-1", {"prompt": "hi"}, timeout=30)
    assert result == {"output": "done"}


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


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_job_status(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "COMPLETED", "output": "ok"}
    mock_get.return_value = mock_resp

    result = client.endpoint_job_status("ep-1", "job-1")
    assert result == {"status": "COMPLETED", "output": "ok"}


@patch("rpctl.api.rest_client.httpx.post")
def test_endpoint_job_cancel(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "CANCELLED"}
    mock_post.return_value = mock_resp

    result = client.endpoint_job_cancel("ep-1", "job-1")
    assert result == {"status": "CANCELLED"}


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_stream(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"stream": [{"output": "chunk1"}, {"output": "chunk2"}]}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == [{"output": "chunk1"}, {"output": "chunk2"}]


@patch("rpctl.api.rest_client.httpx.get")
def test_endpoint_stream_empty(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    result = client.endpoint_stream("ep-1", "job-1")
    assert result == []


# --- Registry auth tests ---


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
    client._gql.execute.return_value = {"saveRegistryAuth": {"id": "ra-1", "name": "docker"}}
    result = client.create_registry_auth("docker", "user", "pass")
    assert result == {"id": "ra-1", "name": "docker"}
    call_args = client._gql.execute.call_args[0][0]
    assert "saveRegistryAuth" in call_args


def test_update_registry_auth(client):
    client._gql.execute.return_value = {"updateRegistryAuth": {"id": "ra-1", "name": "docker"}}
    result = client.update_registry_auth("ra-1", "newuser", "newpass")
    assert result == {"id": "ra-1", "name": "docker"}
    call_args = client._gql.execute.call_args[0][0]
    assert "updateRegistryAuth" in call_args


def test_delete_registry_auth(client):
    client._gql.execute.return_value = {"deleteRegistryAuth": None}
    result = client.delete_registry_auth("ra-1")
    assert result == {"deleteRegistryAuth": None}
    call_args = client._gql.execute.call_args[0][0]
    assert "deleteRegistryAuth" in call_args


# --- User tests ---


def test_get_user(client):
    client._gql.execute.return_value = {"myself": {"id": "user-1", "pubKey": "ssh-rsa AAAA"}}
    result = client.get_user()
    assert result == {"id": "user-1", "pubKey": "ssh-rsa AAAA"}


def test_update_user_settings(client):
    client._gql.execute.return_value = {"updateUserSettings": {"id": "user-1", "pubKey": "ssh-rsa AAAA"}}
    result = client.update_user_settings("ssh-rsa AAAA")
    assert result == {"id": "user-1", "pubKey": "ssh-rsa AAAA"}
    call_args = client._gql.execute.call_args[0][0]
    assert "updateUserSettings" in call_args
