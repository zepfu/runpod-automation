"""Unit tests for RestClient error handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rpctl.api.rest_client import _extract_status_code
from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError


@pytest.fixture
def client():
    """Create a RestClient with a mocked runpod SDK."""
    with patch("rpctl.api.rest_client.runpod", create=True):
        from rpctl.api.rest_client import RestClient

        c = RestClient.__new__(RestClient)
        c._runpod = MagicMock()
        return c


@patch("rpctl.api.retry.time.sleep")
def test_call_success(mock_sleep, client):
    """Successful SDK call returns result."""
    mock_fn = MagicMock(return_value={"id": "pod-1"})
    result = client._call(mock_fn)
    assert result == {"id": "pod-1"}
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_auth_error_401(mock_sleep, client):
    """Exception with '401' raises AuthenticationError."""
    mock_fn = MagicMock(side_effect=Exception("401 Unauthorized"))
    with pytest.raises(AuthenticationError, match="Invalid API key"):
        client._call(mock_fn)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_auth_error_unauthorized(mock_sleep, client):
    """Exception with 'unauthorized' raises AuthenticationError."""
    mock_fn = MagicMock(side_effect=Exception("Request unauthorized"))
    with pytest.raises(AuthenticationError, match="Invalid API key"):
        client._call(mock_fn)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_not_found_404(mock_sleep, client):
    """Exception with '404' raises ResourceNotFoundError."""
    mock_fn = MagicMock(side_effect=Exception("404 Not Found"))
    with pytest.raises(ResourceNotFoundError):
        client._call(mock_fn)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_not_found_message(mock_sleep, client):
    """Exception with 'not found' raises ResourceNotFoundError."""
    mock_fn = MagicMock(side_effect=Exception("Resource not found"))
    with pytest.raises(ResourceNotFoundError):
        client._call(mock_fn)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_generic_error(mock_sleep, client):
    """Other exceptions raise ApiError."""
    mock_fn = MagicMock(side_effect=Exception("Something went wrong"))
    with pytest.raises(ApiError, match="RunPod API error"):
        client._call(mock_fn)
    mock_sleep.assert_not_called()


@patch("rpctl.api.retry.time.sleep")
def test_call_server_error_retried(mock_sleep, client):
    """SDK exception with 500 status code should be retried."""
    call_count = 0

    def flaky(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("500 Internal Server Error")
        return {"id": "pod-1"}

    mock_fn = MagicMock(side_effect=flaky)
    result = client._call(mock_fn)
    assert result == {"id": "pod-1"}
    assert mock_sleep.call_count == 1


@patch("rpctl.api.retry.time.sleep")
def test_get_pod_not_found_empty(mock_sleep, client):
    """get_pod with falsy return raises ResourceNotFoundError."""
    client._runpod.get_pod = MagicMock(return_value=None)
    with pytest.raises(ResourceNotFoundError, match="Pod 'xyz' not found"):
        client.get_pod("xyz")


@patch("rpctl.api.retry.time.sleep")
def test_get_endpoint_not_found_empty(mock_sleep, client):
    """get_endpoint with falsy return raises ResourceNotFoundError."""
    client._runpod.get_endpoint = MagicMock(return_value=None)
    with pytest.raises(ResourceNotFoundError, match="Endpoint 'ep-1' not found"):
        client.get_endpoint("ep-1")


@patch("rpctl.api.retry.time.sleep")
def test_get_template_not_found_empty(mock_sleep, client):
    """get_template with falsy return raises ResourceNotFoundError."""
    client._runpod.get_template = MagicMock(return_value=None)
    with pytest.raises(ResourceNotFoundError, match="Template 'tmpl-1' not found"):
        client.get_template("tmpl-1")


@patch("rpctl.api.retry.time.sleep")
def test_get_volume_not_found_empty(mock_sleep, client):
    """get_volume with falsy return raises ResourceNotFoundError."""
    client._runpod.get_network_volume = MagicMock(return_value=None)
    with pytest.raises(ResourceNotFoundError, match="Volume 'vol-1' not found"):
        client.get_volume("vol-1")


# --- _extract_status_code tests ---


def test_extract_status_code_500():
    assert _extract_status_code("500 Internal Server Error") == 500


def test_extract_status_code_429():
    assert _extract_status_code("HTTP 429 Too Many Requests") == 429


def test_extract_status_code_none():
    assert _extract_status_code("Something went wrong") is None


def test_extract_status_code_401():
    assert _extract_status_code("401 Unauthorized") == 401


def test_extract_status_code_in_longer_message():
    assert _extract_status_code("Request failed with status 503: Service Unavailable") == 503


# --- RestClient __init__ ---


def test_init_sets_api_key():
    """__init__ imports runpod and sets the api_key."""
    mock_runpod = MagicMock()
    with patch.dict("sys.modules", {"runpod": mock_runpod}):
        from rpctl.api.rest_client import RestClient

        c = RestClient("my-api-key")
        assert mock_runpod.api_key == "my-api-key"
        assert c._runpod is mock_runpod


# --- Wrapper method pass-through tests ---


@patch("rpctl.api.retry.time.sleep")
def test_get_pods(mock_sleep, client):
    client._runpod.get_pods.return_value = [{"id": "p1"}]
    result = client.get_pods()
    assert result == [{"id": "p1"}]
    client._runpod.get_pods.assert_called_once()


@patch("rpctl.api.retry.time.sleep")
def test_get_pod_success(mock_sleep, client):
    client._runpod.get_pod.return_value = {"id": "p1"}
    result = client.get_pod("p1")
    assert result == {"id": "p1"}


@patch("rpctl.api.retry.time.sleep")
def test_create_pod(mock_sleep, client):
    client._runpod.create_pod.return_value = {"id": "p1"}
    result = client.create_pod(name="test", image_name="img")
    assert result == {"id": "p1"}
    client._runpod.create_pod.assert_called_once_with(name="test", image_name="img")


@patch("rpctl.api.retry.time.sleep")
def test_stop_pod(mock_sleep, client):
    client._runpod.stop_pod.return_value = {}
    result = client.stop_pod("p1")
    assert result == {}
    client._runpod.stop_pod.assert_called_once_with("p1")


@patch("rpctl.api.retry.time.sleep")
def test_resume_pod(mock_sleep, client):
    client._runpod.resume_pod.return_value = {}
    result = client.resume_pod("p1")
    assert result == {}
    client._runpod.resume_pod.assert_called_once_with("p1")


@patch("rpctl.api.retry.time.sleep")
def test_terminate_pod(mock_sleep, client):
    client._runpod.terminate_pod.return_value = {}
    result = client.terminate_pod("p1")
    assert result == {}
    client._runpod.terminate_pod.assert_called_once_with("p1")


@patch("rpctl.api.retry.time.sleep")
def test_get_endpoints(mock_sleep, client):
    client._runpod.get_endpoints.return_value = [{"id": "ep1"}]
    result = client.get_endpoints()
    assert result == [{"id": "ep1"}]


@patch("rpctl.api.retry.time.sleep")
def test_get_endpoint_success(mock_sleep, client):
    client._runpod.get_endpoint.return_value = {"id": "ep1"}
    result = client.get_endpoint("ep1")
    assert result == {"id": "ep1"}


@patch("rpctl.api.retry.time.sleep")
def test_create_endpoint(mock_sleep, client):
    client._runpod.create_endpoint.return_value = {"id": "ep1"}
    result = client.create_endpoint(name="test", template_id="t1")
    assert result == {"id": "ep1"}


@patch("rpctl.api.retry.time.sleep")
def test_update_endpoint(mock_sleep, client):
    client._runpod.update_endpoint_template.return_value = {"id": "ep1"}
    result = client.update_endpoint("ep1", workers_max=10)
    assert result == {"id": "ep1"}


@patch("rpctl.api.retry.time.sleep")
def test_delete_endpoint(mock_sleep, client):
    client._runpod.delete_endpoint.return_value = {}
    result = client.delete_endpoint("ep1")
    assert result == {}


@patch("rpctl.api.retry.time.sleep")
def test_get_templates(mock_sleep, client):
    client._runpod.get_templates.return_value = [{"id": "t1"}]
    result = client.get_templates()
    assert result == [{"id": "t1"}]


@patch("rpctl.api.retry.time.sleep")
def test_get_template_success(mock_sleep, client):
    client._runpod.get_template.return_value = {"id": "t1"}
    result = client.get_template("t1")
    assert result == {"id": "t1"}


@patch("rpctl.api.retry.time.sleep")
def test_create_template(mock_sleep, client):
    client._runpod.create_template.return_value = {"id": "t1"}
    result = client.create_template(name="test", image_name="img")
    assert result == {"id": "t1"}


@patch("rpctl.api.retry.time.sleep")
def test_update_template(mock_sleep, client):
    client._runpod.update_template.return_value = {"id": "t1"}
    result = client.update_template("t1", name="updated")
    assert result == {"id": "t1"}


@patch("rpctl.api.retry.time.sleep")
def test_delete_template(mock_sleep, client):
    client._runpod.delete_template.return_value = {}
    result = client.delete_template("t1")
    assert result == {}


@patch("rpctl.api.retry.time.sleep")
def test_get_volumes(mock_sleep, client):
    client._runpod.get_network_volumes.return_value = [{"id": "v1"}]
    result = client.get_volumes()
    assert result == [{"id": "v1"}]


@patch("rpctl.api.retry.time.sleep")
def test_get_volume_success(mock_sleep, client):
    client._runpod.get_network_volume.return_value = {"id": "v1"}
    result = client.get_volume("v1")
    assert result == {"id": "v1"}


@patch("rpctl.api.retry.time.sleep")
def test_create_volume(mock_sleep, client):
    client._runpod.create_network_volume.return_value = {"id": "v1"}
    result = client.create_volume(name="test", size=100, data_center_id="US-TX-3")
    assert result == {"id": "v1"}


@patch("rpctl.api.retry.time.sleep")
def test_update_volume(mock_sleep, client):
    client._runpod.update_network_volume.return_value = {"id": "v1"}
    result = client.update_volume("v1", name="updated")
    assert result == {"id": "v1"}


@patch("rpctl.api.retry.time.sleep")
def test_delete_volume(mock_sleep, client):
    client._runpod.delete_network_volume.return_value = {}
    result = client.delete_volume("v1")
    assert result == {}


@patch("rpctl.api.retry.time.sleep")
def test_get_gpus(mock_sleep, client):
    client._runpod.get_gpus.return_value = [{"id": "A100"}]
    result = client.get_gpus()
    assert result == [{"id": "A100"}]


@patch("rpctl.api.retry.time.sleep")
def test_get_gpu(mock_sleep, client):
    client._runpod.get_gpu.return_value = {"id": "A100"}
    result = client.get_gpu("A100")
    assert result == {"id": "A100"}
    client._runpod.get_gpu.assert_called_once_with("A100")
