"""Resource guardrails configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GuardrailsConfig(BaseModel):
    """Configurable limits to prevent accidental resource over-provisioning."""

    allowed_gpu_types: list[str] | None = None  # None = all allowed
    max_gpu_count: int | None = None
    allowed_cpu_types: list[str] | None = None
    max_vcpu: int | None = None
    max_ram_gb: int | None = None
    max_hourly_spend: float | None = None  # USD per hour

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuardrailsConfig:
        """Create from config YAML guardrails section."""
        if not data:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})

    def is_empty(self) -> bool:
        """Check if no guardrails are configured."""
        return all(v is None for v in self.model_dump().values())
