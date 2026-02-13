"""REST API client wrapping the RunPod Python SDK."""

from __future__ import annotations

import logging
import re
from typing import Any

from rpctl.errors import ApiError, AuthenticationError, ResourceNotFoundError

logger = logging.getLogger(__name__)

_STATUS_CODE_RE = re.compile(r"\b(4\d{2}|5\d{2})\b")


def _extract_status_code(msg: str) -> int | None:
    """Best-effort extraction of HTTP status code from SDK error messages."""
    match = _STATUS_CODE_RE.search(msg)
    return int(match.group()) if match else None


class RestClient:
    """Wraps the runpod SDK to isolate its global state and provide consistent error handling."""

    def __init__(self, api_key: str) -> None:
        import runpod

        runpod.api_key = api_key
        self._runpod: Any = runpod

    # --- Pods ---

    def get_pods(self) -> list[dict[str, Any]]:
        return self._call(self._runpod.get_pods)  # type: ignore[no-any-return]

    def get_pod(self, pod_id: str) -> dict[str, Any]:
        result: Any = self._call(self._runpod.get_pod, pod_id)
        if not result:
            raise ResourceNotFoundError(f"Pod '{pod_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_pod(self, **kwargs: Any) -> dict[str, Any]:
        return self._call(self._runpod.create_pod, **kwargs)  # type: ignore[no-any-return]

    def stop_pod(self, pod_id: str) -> dict[str, Any]:
        return self._call(self._runpod.stop_pod, pod_id)  # type: ignore[no-any-return]

    def resume_pod(self, pod_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._call(self._runpod.resume_pod, pod_id, **kwargs)  # type: ignore[no-any-return]

    def terminate_pod(self, pod_id: str) -> dict[str, Any]:
        return self._call(self._runpod.terminate_pod, pod_id)  # type: ignore[no-any-return]

    # --- Endpoints ---

    def get_endpoints(self) -> list[dict[str, Any]]:
        return self._call(self._runpod.get_endpoints)  # type: ignore[no-any-return]

    def get_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        result: Any = self._call(self._runpod.get_endpoint, endpoint_id)
        if not result:
            raise ResourceNotFoundError(f"Endpoint '{endpoint_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_endpoint(self, **kwargs: Any) -> dict[str, Any]:
        return self._call(self._runpod.create_endpoint, **kwargs)  # type: ignore[no-any-return]

    def update_endpoint(self, endpoint_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.update_endpoint_template, endpoint_id, **kwargs
        )

    def delete_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        return self._call(self._runpod.delete_endpoint, endpoint_id)  # type: ignore[no-any-return]

    def endpoint_health(self, endpoint_id: str) -> dict[str, Any]:
        ep = self._runpod.Endpoint(endpoint_id)
        return self._call(ep.health)  # type: ignore[no-any-return]

    def endpoint_run_sync(
        self, endpoint_id: str, request_input: dict[str, Any], timeout: int = 86400
    ) -> dict[str, Any]:
        ep = self._runpod.Endpoint(endpoint_id)
        return self._call(ep.run_sync, request_input, timeout)  # type: ignore[no-any-return]

    def endpoint_run_async(self, endpoint_id: str, request_input: dict[str, Any]) -> str:
        ep = self._runpod.Endpoint(endpoint_id)
        job = self._call(ep.run, request_input)
        return job.job_id  # type: ignore[no-any-return]

    def endpoint_purge_queue(self, endpoint_id: str) -> dict[str, Any]:
        ep = self._runpod.Endpoint(endpoint_id)
        return self._call(ep.purge_queue)  # type: ignore[no-any-return]

    # --- Templates ---

    def get_templates(self) -> list[dict[str, Any]]:
        return self._call(self._runpod.get_templates)  # type: ignore[no-any-return]

    def get_template(self, template_id: str) -> dict[str, Any]:
        result: Any = self._call(self._runpod.get_template, template_id)
        if not result:
            raise ResourceNotFoundError(f"Template '{template_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_template(self, **kwargs: Any) -> dict[str, Any]:
        return self._call(self._runpod.create_template, **kwargs)  # type: ignore[no-any-return]

    def update_template(self, template_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.update_template, template_id, **kwargs
        )

    def delete_template(self, template_id: str) -> dict[str, Any]:
        return self._call(self._runpod.delete_template, template_id)  # type: ignore[no-any-return]

    # --- Network Volumes ---

    def get_volumes(self) -> list[dict[str, Any]]:
        return self._call(self._runpod.get_network_volumes)  # type: ignore[no-any-return]

    def get_volume(self, volume_id: str) -> dict[str, Any]:
        result: Any = self._call(self._runpod.get_network_volume, volume_id)
        if not result:
            raise ResourceNotFoundError(f"Volume '{volume_id}' not found.")
        return result  # type: ignore[no-any-return]

    def create_volume(self, **kwargs: Any) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.create_network_volume, **kwargs
        )

    def update_volume(self, volume_id: str, **kwargs: Any) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.update_network_volume, volume_id, **kwargs
        )

    def delete_volume(self, volume_id: str) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.delete_network_volume, volume_id
        )

    # --- GPU info ---

    def get_gpus(self) -> list[dict[str, Any]]:
        return self._call(self._runpod.get_gpus)  # type: ignore[no-any-return]

    def get_gpu(self, gpu_id: str) -> dict[str, Any]:
        return self._call(self._runpod.get_gpu, gpu_id)  # type: ignore[no-any-return]

    # --- Container Registry Auth ---

    def create_registry_auth(self, name: str, username: str, password: str) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.create_container_registry_auth, name, username, password
        )

    def update_registry_auth(
        self, registry_auth_id: str, username: str, password: str
    ) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.update_container_registry_auth, registry_auth_id, username, password
        )

    def delete_registry_auth(self, registry_auth_id: str) -> dict[str, Any]:
        return self._call(  # type: ignore[no-any-return]
            self._runpod.delete_container_registry_auth, registry_auth_id
        )

    # --- User ---

    def get_user(self) -> dict[str, Any]:
        return self._call(self._runpod.get_user)  # type: ignore[no-any-return]

    def update_user_settings(self, pubkey: str) -> dict[str, Any]:
        return self._call(self._runpod.update_user_settings, pubkey)  # type: ignore[no-any-return]

    def _call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Call a runpod SDK function with retry on transient errors."""
        from rpctl.api.retry import retry_on_transient

        return retry_on_transient(self._call_once, func, *args, **kwargs)

    def _call_once(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Call a runpod SDK function with error handling (no retry)."""
        logger.debug("SDK call: %s", func.__name__ if hasattr(func, "__name__") else func)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            if "401" in msg or "unauthorized" in msg.lower():
                raise AuthenticationError("Invalid API key.") from e
            if "404" in msg or "not found" in msg.lower():
                raise ResourceNotFoundError(msg) from e
            status_code = _extract_status_code(msg)
            raise ApiError(f"RunPod API error: {msg}", status_code=status_code) from e
