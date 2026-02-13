"""Unit tests for GraphQLClient HTTP scenarios."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx
from rpctl.api.graphql_client import GraphQLClient
from rpctl.errors import ApiError, AuthenticationError

GQL_URL = "https://api.runpod.io/graphql/"
QUERY = "query { gpuTypes { id } }"


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_success(mock_sleep):
    """Successful GraphQL response returns data."""
    respx.post(GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"gpuTypes": [{"id": "A100"}]}})
    )
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {"gpuTypes": [{"id": "A100"}]}
    mock_sleep.assert_not_called()


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_with_variables(mock_sleep):
    """Query variables are included in the request payload."""
    route = respx.post(GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"pod": {"id": "pod-1"}}})
    )
    client = GraphQLClient("test-key")
    result = client.execute("query($id: String!) { pod(id: $id) { id } }", {"id": "pod-1"})
    assert result == {"pod": {"id": "pod-1"}}
    payload = route.calls[0].request.content
    assert b"variables" in payload


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_auth_error(mock_sleep):
    """401 response raises AuthenticationError (no retry)."""
    respx.post(GQL_URL).mock(return_value=httpx.Response(401))
    client = GraphQLClient("bad-key")
    with pytest.raises(AuthenticationError, match="Invalid API key"):
        client.execute(QUERY)
    mock_sleep.assert_not_called()


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_rate_limited_429(mock_sleep):
    """429 response raises transient ApiError with status_code."""
    respx.post(GQL_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(429, headers={"Retry-After": "3"}),
        ]
    )
    client = GraphQLClient("test-key")
    with pytest.raises(ApiError, match="Rate limited") as exc_info:
        client.execute(QUERY)
    assert exc_info.value.status_code == 429
    assert exc_info.value.is_transient


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_429_then_success(mock_sleep):
    """429 followed by success should work via retry."""
    respx.post(GQL_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json={"data": {"gpuTypes": []}}),
        ]
    )
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {"gpuTypes": []}
    assert mock_sleep.call_count == 1


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_server_error_500(mock_sleep):
    """500 response is transient and retried."""
    respx.post(GQL_URL).mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(200, json={"data": {"ok": True}}),
        ]
    )
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {"ok": True}
    assert mock_sleep.call_count == 1


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_server_error_503_exhausted(mock_sleep):
    """503 across all attempts raises ApiError."""
    respx.post(GQL_URL).mock(return_value=httpx.Response(503))
    client = GraphQLClient("test-key")
    with pytest.raises(ApiError) as exc_info:
        client.execute(QUERY)
    assert exc_info.value.status_code == 503


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_graphql_body_errors(mock_sleep):
    """GraphQL errors in response body raise ApiError (not retried)."""
    respx.post(GQL_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "errors": [{"message": "Field 'foo' not found"}],
            },
        )
    )
    client = GraphQLClient("test-key")
    with pytest.raises(ApiError, match="Field 'foo' not found"):
        client.execute(QUERY)
    mock_sleep.assert_not_called()


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_connect_error(mock_sleep):
    """Connection error is retried as transient."""
    call_count = 0
    original_side_effects = [
        httpx.ConnectError("Connection refused"),
        httpx.Response(200, json={"data": {"ok": True}}),
    ]

    def side_effect(request):
        nonlocal call_count
        result = original_side_effects[call_count]
        call_count += 1
        if isinstance(result, Exception):
            raise result
        return result

    respx.post(GQL_URL).mock(side_effect=side_effect)
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {"ok": True}
    assert mock_sleep.call_count == 1


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_timeout(mock_sleep):
    """Timeout is retried as transient."""
    call_count = 0
    original_side_effects = [
        httpx.ReadTimeout("timed out"),
        httpx.Response(200, json={"data": {"ok": True}}),
    ]

    def side_effect(request):
        nonlocal call_count
        result = original_side_effects[call_count]
        call_count += 1
        if isinstance(result, Exception):
            raise result
        return result

    respx.post(GQL_URL).mock(side_effect=side_effect)
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {"ok": True}
    assert mock_sleep.call_count == 1


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_non_200_non_transient(mock_sleep):
    """400 response raises immediately (not retried)."""
    respx.post(GQL_URL).mock(return_value=httpx.Response(400))
    client = GraphQLClient("test-key")
    with pytest.raises(ApiError) as exc_info:
        client.execute(QUERY)
    assert exc_info.value.status_code == 400
    assert not exc_info.value.is_transient
    mock_sleep.assert_not_called()


def test_context_manager():
    """GraphQLClient works as a context manager."""
    with GraphQLClient("test-key") as client:
        assert client is not None


@respx.mock
@patch("rpctl.api.retry.time.sleep")
def test_execute_empty_data(mock_sleep):
    """Response with no data key returns empty dict."""
    respx.post(GQL_URL).mock(return_value=httpx.Response(200, json={}))
    client = GraphQLClient("test-key")
    result = client.execute(QUERY)
    assert result == {}
