"""API client using GraphQL and httpx REST calls."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError

logger = logging.getLogger(__name__)

_ENDPOINT_REST_BASE = "https://api.runpod.ai/v2"


class RestClient:
    """Unified API client using GraphQL for management and httpx for endpoint REST calls."""

    def __init__(self, api_key: str) -> None:
        from rpctl.api.graphql_client import GraphQLClient

        self._api_key = api_key
        self._gql = GraphQLClient(api_key)

    # --- Pods ---

    def get_pods(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import POD_LIST

        data = self._gql.execute(POD_LIST)
        return data.get("myself", {}).get("pods", [])  # type: ignore[no-any-return]

    def get_pod(self, pod_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_get_query

        query = build_pod_get_query(pod_id)
        data = self._gql.execute(query)
        result = data.get("pod")
        if not result:
            raise ResourceNotFoundError(f"Pod '{pod_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_pod(self, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_create_mutation

        query = build_pod_create_mutation(**kwargs)
        data = self._gql.execute(query)
        # Mutation returns podFindAndDeployOnDemand or deployCpuPod
        return data.get("podFindAndDeployOnDemand") or data.get("deployCpuPod") or {}

    def stop_pod(self, pod_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_stop_mutation

        query = build_pod_stop_mutation(pod_id)
        data = self._gql.execute(query)
        return data.get("podStop", {})  # type: ignore[no-any-return]

    def resume_pod(self, pod_id: str, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_resume_mutation

        gpu_count = kwargs.get("gpu_count", 1)
        query = build_pod_resume_mutation(pod_id, gpu_count=gpu_count)
        data = self._gql.execute(query)
        return data.get("podResume", {})  # type: ignore[no-any-return]

    def terminate_pod(self, pod_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_terminate_mutation

        query = build_pod_terminate_mutation(pod_id)
        data = self._gql.execute(query)
        return data

    def edit_pod(self, pod_id: str, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_edit_mutation

        query = build_pod_edit_mutation(pod_id, **kwargs)
        data = self._gql.execute(query)
        return data.get("podEditJob", {})  # type: ignore[no-any-return]

    def migrate_pod(
        self, pod_id: str, gpu_type_id: str | None = None, bid_per_gpu: float | None = None
    ) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_migrate_mutation

        query = build_pod_migrate_mutation(pod_id, gpu_type_id=gpu_type_id, bid_per_gpu=bid_per_gpu)
        data = self._gql.execute(query)
        return data.get("podBidResume", {})  # type: ignore[no-any-return]

    def reset_pod(self, pod_id: str, hard_reset: bool = False) -> dict[str, Any]:
        from rpctl.api.queries import build_pod_reset_mutation

        query = build_pod_reset_mutation(pod_id, hard_reset=hard_reset)
        data = self._gql.execute(query)
        return data

    # --- Endpoints ---

    def get_endpoints(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import ENDPOINT_LIST

        data = self._gql.execute(ENDPOINT_LIST)
        return data.get("myself", {}).get("endpoints", [])  # type: ignore[no-any-return]

    def get_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        endpoints = self.get_endpoints()
        for ep in endpoints:
            if ep.get("id") == endpoint_id:
                return ep
        raise ResourceNotFoundError(f"Endpoint '{endpoint_id}' not found.")

    def create_endpoint(self, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_save_endpoint_mutation

        query = build_save_endpoint_mutation(kwargs)
        data = self._gql.execute(query)
        return data.get("saveEndpoint", {})  # type: ignore[no-any-return]

    def update_endpoint(self, endpoint_id: str, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_save_endpoint_mutation

        params: dict[str, Any] = {"id": endpoint_id, **kwargs}
        query = build_save_endpoint_mutation(params)
        data = self._gql.execute(query)
        return data.get("saveEndpoint", {})  # type: ignore[no-any-return]

    def delete_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_delete_endpoint_mutation

        query = build_delete_endpoint_mutation(endpoint_id)
        data = self._gql.execute(query)
        return data

    def endpoint_health(self, endpoint_id: str) -> dict[str, Any]:
        return self._endpoint_rest("GET", f"{endpoint_id}/health", timeout=3)

    def endpoint_run_sync(
        self, endpoint_id: str, request_input: dict[str, Any], timeout: int = 86400
    ) -> dict[str, Any]:
        if not request_input.get("input"):
            request_input = {"input": request_input}
        return self._endpoint_rest("POST", f"{endpoint_id}/runsync", json=request_input, timeout=timeout)

    def endpoint_run_async(self, endpoint_id: str, request_input: dict[str, Any]) -> str:
        if not request_input.get("input"):
            request_input = {"input": request_input}
        result = self._endpoint_rest("POST", f"{endpoint_id}/run", json=request_input)
        return result.get("id", "")  # type: ignore[no-any-return]

    def endpoint_purge_queue(self, endpoint_id: str) -> dict[str, Any]:
        return self._endpoint_rest("POST", f"{endpoint_id}/purge-queue", timeout=3)

    def endpoint_job_status(self, endpoint_id: str, job_id: str) -> dict[str, Any]:
        return self._endpoint_rest("GET", f"{endpoint_id}/status/{job_id}")

    def endpoint_job_cancel(self, endpoint_id: str, job_id: str) -> dict[str, Any]:
        return self._endpoint_rest("POST", f"{endpoint_id}/cancel/{job_id}")

    def endpoint_stream(self, endpoint_id: str, job_id: str) -> list[dict[str, Any]]:
        """Stream output from a running job. Returns list of output chunks."""
        data = self._endpoint_rest("GET", f"{endpoint_id}/stream/{job_id}")
        return data.get("stream", [])  # type: ignore[no-any-return]

    # --- Templates ---

    def get_templates(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import TEMPLATE_LIST

        data = self._gql.execute(TEMPLATE_LIST)
        return data.get("podTemplates", [])  # type: ignore[no-any-return]

    def get_template(self, template_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_template_get_query

        query = build_template_get_query(template_id)
        data = self._gql.execute(query)
        result = data.get("podTemplate")
        if not result:
            raise ResourceNotFoundError(f"Template '{template_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_template(self, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_save_template_mutation

        query = build_save_template_mutation(kwargs)
        data = self._gql.execute(query)
        return data.get("saveTemplate", {})  # type: ignore[no-any-return]

    def update_template(self, template_id: str, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_save_template_mutation

        params: dict[str, Any] = {"id": template_id, **kwargs}
        query = build_save_template_mutation(params)
        data = self._gql.execute(query)
        return data.get("saveTemplate", {})  # type: ignore[no-any-return]

    def delete_template(self, template_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_delete_template_mutation

        template = self.get_template(template_id)
        template_name = template.get("name", "")
        if not template_name:
            raise ApiError(f"Cannot delete template '{template_id}': name not found.")
        query = build_delete_template_mutation(template_name)
        data = self._gql.execute(query)
        return data

    # --- Network Volumes ---

    def get_volumes(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import VOLUME_LIST

        data = self._gql.execute(VOLUME_LIST)
        return data.get("myself", {}).get("networkVolumes", [])  # type: ignore[no-any-return]

    def get_volume(self, volume_id: str) -> dict[str, Any]:
        volumes = self.get_volumes()
        for v in volumes:
            if v.get("id") == volume_id:
                return v
        raise ResourceNotFoundError(f"Volume '{volume_id}' not found.")

    def create_volume(self, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_create_volume_mutation

        query = build_create_volume_mutation(
            name=kwargs["name"],
            size=kwargs["size"],
            data_center_id=kwargs["data_center_id"],
        )
        data = self._gql.execute(query)
        return data.get("createNetworkVolume", {})  # type: ignore[no-any-return]

    def update_volume(self, volume_id: str, **kwargs: Any) -> dict[str, Any]:
        from rpctl.api.queries import build_update_volume_mutation

        query = build_update_volume_mutation(volume_id, **kwargs)
        data = self._gql.execute(query)
        return data.get("updateNetworkVolume", {})  # type: ignore[no-any-return]

    def delete_volume(self, volume_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_delete_volume_mutation

        query = build_delete_volume_mutation(volume_id)
        data = self._gql.execute(query)
        return data

    # --- Account ---

    def get_account_info(self) -> dict[str, Any]:
        from rpctl.api.queries import ACCOUNT_INFO

        data = self._gql.execute(ACCOUNT_INFO)
        return data.get("myself", {})  # type: ignore[no-any-return]

    # --- Secrets ---

    def get_secrets(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import SECRETS_LIST

        data = self._gql.execute(SECRETS_LIST)
        return data.get("myself", {}).get("secrets", [])  # type: ignore[no-any-return]

    def add_secret(self, name: str, value: str) -> dict[str, Any]:
        from rpctl.api.queries import build_add_secret_mutation

        query = build_add_secret_mutation(name, value)
        data = self._gql.execute(query)
        return data

    def delete_secret(self, name: str) -> dict[str, Any]:
        from rpctl.api.queries import build_delete_secret_mutation

        query = build_delete_secret_mutation(name)
        data = self._gql.execute(query)
        return data

    # --- GPU info ---

    def get_gpus(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import GPU_TYPES_LIST

        data = self._gql.execute(GPU_TYPES_LIST)
        return data.get("gpuTypes", [])  # type: ignore[no-any-return]

    def get_gpu(self, gpu_id: str) -> dict[str, Any]:
        from rpctl.api.queries import GPU_TYPE_AVAILABILITY

        data = self._gql.execute(
            GPU_TYPE_AVAILABILITY,
            {"gpuTypeId": gpu_id, "gpuCount": 1, "secureCloud": None},
        )
        types = data.get("gpuTypes", [])
        if types:
            return types[0]  # type: ignore[no-any-return]
        return {}

    # --- Container Registry Auth ---

    def list_registry_auths(self) -> list[dict[str, Any]]:
        from rpctl.api.queries import REGISTRY_AUTH_LIST

        data = self._gql.execute(REGISTRY_AUTH_LIST)
        return data.get("myself", {}).get("containerRegistryAuths", [])  # type: ignore[no-any-return]

    def create_registry_auth(self, name: str, username: str, password: str) -> dict[str, Any]:
        from rpctl.api.queries import build_create_registry_auth_mutation

        query = build_create_registry_auth_mutation(name, username, password)
        data = self._gql.execute(query)
        return data.get("saveRegistryAuth", {})  # type: ignore[no-any-return]

    def update_registry_auth(
        self, registry_auth_id: str, username: str, password: str
    ) -> dict[str, Any]:
        from rpctl.api.queries import build_update_registry_auth_mutation

        query = build_update_registry_auth_mutation(registry_auth_id, username, password)
        data = self._gql.execute(query)
        return data.get("updateRegistryAuth", {})  # type: ignore[no-any-return]

    def delete_registry_auth(self, registry_auth_id: str) -> dict[str, Any]:
        from rpctl.api.queries import build_delete_registry_auth_mutation

        query = build_delete_registry_auth_mutation(registry_auth_id)
        data = self._gql.execute(query)
        return data

    # --- User ---

    def get_user(self) -> dict[str, Any]:
        from rpctl.api.queries import USER_INFO

        data = self._gql.execute(USER_INFO)
        return data.get("myself", {})  # type: ignore[no-any-return]

    def update_user_settings(self, pubkey: str) -> dict[str, Any]:
        from rpctl.api.queries import build_update_user_settings_mutation

        query = build_update_user_settings_mutation(pubkey)
        data = self._gql.execute(query)
        return data.get("updateUserSettings", {})  # type: ignore[no-any-return]

    # --- Internal helpers ---

    def _endpoint_rest(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Make a REST call to the RunPod endpoint API."""
        url = f"{_ENDPOINT_REST_BASE}/{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            if method == "GET":
                resp = httpx.get(url, headers=headers, timeout=timeout)
            else:
                resp = httpx.post(url, headers=headers, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API key.") from e
            if e.response.status_code == 404:
                raise ResourceNotFoundError(f"Not found: {path}") from e
            raise ApiError(
                f"Endpoint API error: {e.response.status_code}",
                status_code=e.response.status_code,
            ) from e
        except httpx.ConnectError as e:
            raise ApiError(f"Cannot connect to RunPod API: {e}", status_code=503) from e
        except httpx.TimeoutException as e:
            raise ApiError(f"Request timed out: {e}", status_code=408) from e
