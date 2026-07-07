"""Resource guardrails validation service."""

from __future__ import annotations

from typing import Any

from rpctl.config.guardrails import GuardrailsConfig


class GuardrailsService:
    """Validates resource requests against configured guardrails."""

    def __init__(self, guardrails: GuardrailsConfig) -> None:
        self._guardrails = guardrails

    def validate_pod_create(self, params: dict[str, Any]) -> list[str]:
        """Validate pod create params against guardrails. Returns list of violations."""
        violations: list[str] = []
        g = self._guardrails

        # GPU type check
        if g.allowed_gpu_types is not None:
            gpu_types = params.get("gpu_type_ids", [])
            gpu_type = params.get("gpu_type_id")
            if gpu_type:
                gpu_types = [gpu_type] + gpu_types
            for gt in gpu_types:
                if gt not in g.allowed_gpu_types:
                    violations.append(
                        f"GPU type '{gt}' is not in allowed list: "
                        f"{', '.join(g.allowed_gpu_types)}"
                    )

        # GPU count check
        if g.max_gpu_count is not None:
            gpu_count = params.get("gpu_count", 1)
            if gpu_count > g.max_gpu_count:
                violations.append(
                    f"GPU count {gpu_count} exceeds maximum of {g.max_gpu_count}"
                )

        # CPU type check
        if g.allowed_cpu_types is not None:
            cpu_types = params.get("cpu_flavor_ids", [])
            for ct in cpu_types:
                if ct not in g.allowed_cpu_types:
                    violations.append(
                        f"CPU type '{ct}' is not in allowed list: "
                        f"{', '.join(g.allowed_cpu_types)}"
                    )

        return violations

    def validate_endpoint_create(self, params: dict[str, Any]) -> list[str]:
        """Validate endpoint create params against guardrails. Returns list of violations."""
        violations: list[str] = []
        g = self._guardrails

        # GPU type check for endpoints (gpu_ids field)
        if g.allowed_gpu_types is not None:
            gpu_ids = params.get("gpu_ids")
            if gpu_ids and gpu_ids not in g.allowed_gpu_types:
                violations.append(
                    f"GPU type '{gpu_ids}' is not in allowed list: "
                    f"{', '.join(g.allowed_gpu_types)}"
                )

        # Max GPU count for endpoints
        if g.max_gpu_count is not None:
            gpu_count = params.get("gpu_count", 1)
            if gpu_count > g.max_gpu_count:
                violations.append(
                    f"GPU count {gpu_count} exceeds maximum of {g.max_gpu_count}"
                )

        return violations

    def check_spend_limit(self, account_info: dict[str, Any]) -> list[str]:
        """Check current spend against configured limit. Returns warnings (not hard blocks)."""
        warnings: list[str] = []
        g = self._guardrails

        if g.max_hourly_spend is not None:
            current_spend = account_info.get("currentSpendPerHr", 0) or 0
            if current_spend >= g.max_hourly_spend:
                warnings.append(
                    f"Current hourly spend ${current_spend:.4f}/hr "
                    f"meets or exceeds limit of ${g.max_hourly_spend:.2f}/hr"
                )

        balance = account_info.get("clientBalance", 0) or 0
        if balance <= 0:
            warnings.append(f"Account balance is ${balance:.2f}")

        return warnings
