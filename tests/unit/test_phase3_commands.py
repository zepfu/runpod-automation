"""Tests for Phase 3: Pod edit/migrate/reset mutations and endpoint scale."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rpctl.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# GraphQL query builder tests
# ---------------------------------------------------------------------------


class TestBuildPodEditMutation:
    def test_basic_fields(self) -> None:
        from rpctl.api.queries import build_pod_edit_mutation

        query = build_pod_edit_mutation(
            "pod-123", imageName="ubuntu:22.04", containerDiskInGb=100
        )
        assert 'podId: "pod-123"' in query
        assert 'imageName: "ubuntu:22.04"' in query
        assert "containerDiskInGb: 100" in query
        assert "podEditJob" in query

    def test_with_env(self) -> None:
        from rpctl.api.queries import build_pod_edit_mutation

        env = [{"key": "FOO", "value": "bar"}, {"key": "BAZ", "value": "qux"}]
        query = build_pod_edit_mutation("pod-123", env=env)
        assert 'podId: "pod-123"' in query
        assert 'key: "FOO"' in query
        assert 'value: "bar"' in query
        assert 'key: "BAZ"' in query


class TestBuildPodMigrateMutation:
    def test_with_gpu(self) -> None:
        from rpctl.api.queries import build_pod_migrate_mutation

        query = build_pod_migrate_mutation("pod-123", gpu_type_id="NVIDIA RTX A6000")
        assert 'podId: "pod-123"' in query
        assert 'gpuTypeId: "NVIDIA RTX A6000"' in query
        assert "podBidResume" in query

    def test_with_bid(self) -> None:
        from rpctl.api.queries import build_pod_migrate_mutation

        query = build_pod_migrate_mutation("pod-123", bid_per_gpu=0.5)
        assert 'podId: "pod-123"' in query
        assert "bidPerGpu: 0.5" in query


class TestBuildPodResetMutation:
    def test_soft_reset(self) -> None:
        from rpctl.api.queries import build_pod_reset_mutation

        query = build_pod_reset_mutation("pod-123")
        assert 'podId: "pod-123"' in query
        assert "hardReset: false" in query
        assert "podReset" in query

    def test_hard_reset(self) -> None:
        from rpctl.api.queries import build_pod_reset_mutation

        query = build_pod_reset_mutation("pod-123", hard_reset=True)
        assert "hardReset: true" in query


# ---------------------------------------------------------------------------
# RestClient method tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> MagicMock:
    from rpctl.api.rest_client import RestClient

    c = RestClient.__new__(RestClient)
    c._api_key = "test-key"
    c._gql = MagicMock()
    return c  # type: ignore[return-value]


class TestRestClientPodMutations:
    def test_edit_pod(self, client: MagicMock) -> None:
        client._gql.execute.return_value = {
            "podEditJob": {"id": "pod-123", "imageName": "new-image"}
        }
        result = client.edit_pod("pod-123", imageName="new-image")
        assert result == {"id": "pod-123", "imageName": "new-image"}
        client._gql.execute.assert_called_once()

    def test_migrate_pod(self, client: MagicMock) -> None:
        client._gql.execute.return_value = {
            "podBidResume": {"id": "pod-123", "desiredStatus": "RUNNING"}
        }
        result = client.migrate_pod("pod-123", gpu_type_id="NVIDIA A100")
        assert result == {"id": "pod-123", "desiredStatus": "RUNNING"}
        client._gql.execute.assert_called_once()

    def test_reset_pod(self, client: MagicMock) -> None:
        client._gql.execute.return_value = {"podReset": True}
        result = client.reset_pod("pod-123")
        assert result == {"podReset": True}

    def test_reset_pod_hard(self, client: MagicMock) -> None:
        client._gql.execute.return_value = {"podReset": True}
        client.reset_pod("pod-123", hard_reset=True)
        call_args = client._gql.execute.call_args[0][0]
        assert "hardReset: true" in call_args


# ---------------------------------------------------------------------------
# Service method tests
# ---------------------------------------------------------------------------


class TestPodServiceMutations:
    def test_edit_pod(self) -> None:
        from rpctl.services.pod_service import PodService

        mock_client = MagicMock()
        mock_client.edit_pod.return_value = {"id": "pod-123"}
        svc = PodService(mock_client)
        result = svc.edit_pod("pod-123", imageName="new-image")
        assert result == {"id": "pod-123"}
        mock_client.edit_pod.assert_called_once_with("pod-123", imageName="new-image")

    def test_migrate_pod(self) -> None:
        from rpctl.services.pod_service import PodService

        mock_client = MagicMock()
        mock_client.migrate_pod.return_value = {"id": "pod-123"}
        svc = PodService(mock_client)
        result = svc.migrate_pod("pod-123", gpu_type_id="A100")
        assert result == {"id": "pod-123"}
        mock_client.migrate_pod.assert_called_once_with(
            "pod-123", gpu_type_id="A100", bid_per_gpu=None
        )

    def test_reset_pod(self) -> None:
        from rpctl.services.pod_service import PodService

        mock_client = MagicMock()
        mock_client.reset_pod.return_value = {"podReset": True}
        svc = PodService(mock_client)
        result = svc.reset_pod("pod-123", hard_reset=True)
        assert result == {"podReset": True}
        mock_client.reset_pod.assert_called_once_with("pod-123", hard_reset=True)


class TestEndpointServiceScale:
    def test_scale_endpoint(self) -> None:
        from rpctl.models.endpoint import Endpoint
        from rpctl.services.endpoint_service import EndpointService

        mock_client = MagicMock()
        mock_client.update_endpoint.return_value = {
            "id": "ep-123",
            "name": "test-ep",
            "templateId": "tpl-1",
            "gpuIds": "AMPERE_24",
            "workersMin": 1,
            "workersMax": 5,
        }
        svc = EndpointService(mock_client)
        result = svc.scale_endpoint("ep-123", workers_min=1, workers_max=5)
        assert isinstance(result, Endpoint)
        mock_client.update_endpoint.assert_called_once_with(
            "ep-123", workersMin=1, workersMax=5
        )


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


def _mock_settings() -> MagicMock:
    mock = MagicMock()
    mock.api_key = "test-key"
    mock.active_profile = "default"
    mock.guardrails = MagicMock()
    mock.guardrails.is_empty.return_value = True
    return mock


class TestPodEditCLI:
    def test_success(self) -> None:
        with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.edit_pod.return_value = {
                "id": "pod-123",
                "imageName": "new-image",
                "containerDiskInGb": 100,
            }
            mock_svc_fn.return_value = mock_svc
            result = runner.invoke(
                app, ["pod", "edit", "pod-123", "--image", "new-image", "--container-disk", "100"]
            )
            assert result.exit_code == 0
            assert "updated" in result.output
            mock_svc.edit_pod.assert_called_once_with(
                "pod-123", imageName="new-image", containerDiskInGb=100
            )

    def test_no_params(self) -> None:
        result = runner.invoke(app, ["pod", "edit", "pod-123"])
        assert result.exit_code == 1
        assert "No edit parameters" in result.output


class TestPodMigrateCLI:
    def test_success(self) -> None:
        with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.migrate_pod.return_value = {
                "id": "pod-123",
                "desiredStatus": "RUNNING",
            }
            mock_svc_fn.return_value = mock_svc
            result = runner.invoke(
                app, ["pod", "migrate", "pod-123", "--gpu", "NVIDIA A100"]
            )
            assert result.exit_code == 0
            assert "migration initiated" in result.output
            mock_svc.migrate_pod.assert_called_once_with(
                "pod-123", gpu_type_id="NVIDIA A100", bid_per_gpu=None
            )

    def test_no_params(self) -> None:
        result = runner.invoke(app, ["pod", "migrate", "pod-123"])
        assert result.exit_code == 1
        assert "Provide --gpu" in result.output


class TestPodResetCLI:
    def test_soft_reset(self) -> None:
        with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.reset_pod.return_value = {"podReset": True}
            mock_svc_fn.return_value = mock_svc
            result = runner.invoke(app, ["pod", "reset", "pod-123"])
            assert result.exit_code == 0
            assert "Reset initiated" in result.output
            mock_svc.reset_pod.assert_called_once_with("pod-123", hard_reset=False)

    def test_hard_confirmed(self) -> None:
        with patch("rpctl.cli.pod._get_pod_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.reset_pod.return_value = {"podReset": True}
            mock_svc_fn.return_value = mock_svc
            result = runner.invoke(
                app, ["pod", "reset", "pod-123", "--hard", "--confirm"]
            )
            assert result.exit_code == 0
            assert "Hard reset initiated" in result.output
            mock_svc.reset_pod.assert_called_once_with("pod-123", hard_reset=True)


class TestEndpointScaleCLI:
    def test_success(self) -> None:
        with patch("rpctl.cli.endpoint._get_endpoint_service") as mock_svc_fn:
            mock_svc = MagicMock()
            # Return an Endpoint model
            from rpctl.models.endpoint import Endpoint

            mock_svc.scale_endpoint.return_value = Endpoint(
                id="ep-123",
                name="test-ep",
                template_id="tpl-1",
                gpu_ids="AMPERE_24",
                workers_min=1,
                workers_max=5,
            )
            mock_svc_fn.return_value = mock_svc
            result = runner.invoke(
                app, ["endpoint", "scale", "ep-123", "--min", "1", "--max", "5"]
            )
            assert result.exit_code == 0
            mock_svc.scale_endpoint.assert_called_once_with(
                "ep-123", workers_min=1, workers_max=5
            )

    def test_no_params(self) -> None:
        result = runner.invoke(app, ["endpoint", "scale", "ep-123"])
        assert result.exit_code == 1
        assert "Provide --min" in result.output
