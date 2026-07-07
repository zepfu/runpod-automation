"""Tests for resource guardrails (Phase 2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rpctl.config.guardrails import GuardrailsConfig
from rpctl.main import app
from rpctl.services.guardrails_service import GuardrailsService

runner = CliRunner()


# ---------------------------------------------------------------------------
# GuardrailsConfig model
# ---------------------------------------------------------------------------


class TestGuardrailsConfig:
    def test_empty_guardrails(self) -> None:
        gc = GuardrailsConfig()
        assert gc.allowed_gpu_types is None
        assert gc.max_gpu_count is None
        assert gc.allowed_cpu_types is None
        assert gc.max_vcpu is None
        assert gc.max_ram_gb is None
        assert gc.max_hourly_spend is None

    def test_from_dict_with_values(self) -> None:
        gc = GuardrailsConfig.from_dict(
            {
                "allowed_gpu_types": ["A100", "H100"],
                "max_gpu_count": 4,
                "max_hourly_spend": 2.50,
            }
        )
        assert gc.allowed_gpu_types == ["A100", "H100"]
        assert gc.max_gpu_count == 4
        assert gc.max_hourly_spend == 2.50

    def test_from_dict_ignores_unknown_keys(self) -> None:
        gc = GuardrailsConfig.from_dict(
            {"allowed_gpu_types": ["A100"], "bogus_key": "ignored"}
        )
        assert gc.allowed_gpu_types == ["A100"]

    def test_from_dict_empty(self) -> None:
        gc = GuardrailsConfig.from_dict({})
        assert gc.is_empty()

    def test_from_dict_none(self) -> None:
        gc = GuardrailsConfig.from_dict(None)  # type: ignore[arg-type]
        assert gc.is_empty()

    def test_is_empty_true(self) -> None:
        gc = GuardrailsConfig()
        assert gc.is_empty() is True

    def test_is_empty_false(self) -> None:
        gc = GuardrailsConfig(max_gpu_count=2)
        assert gc.is_empty() is False


# ---------------------------------------------------------------------------
# GuardrailsService — pod create
# ---------------------------------------------------------------------------


class TestValidatePodCreate:
    def test_no_violations_when_empty(self) -> None:
        svc = GuardrailsService(GuardrailsConfig())
        assert svc.validate_pod_create({"gpu_type_ids": ["A100"]}) == []

    def test_gpu_type_violation(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["A100", "H100"])
        )
        violations = svc.validate_pod_create({"gpu_type_ids": ["RTX 4090"]})
        assert len(violations) == 1
        assert "RTX 4090" in violations[0]
        assert "not in allowed list" in violations[0]

    def test_gpu_type_allowed(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["A100", "H100"])
        )
        assert svc.validate_pod_create({"gpu_type_ids": ["A100"]}) == []

    def test_gpu_type_id_field(self) -> None:
        """gpu_type_id (singular) is also checked."""
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["A100"])
        )
        violations = svc.validate_pod_create({"gpu_type_id": "H100"})
        assert len(violations) == 1
        assert "H100" in violations[0]

    def test_gpu_count_violation(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_gpu_count=2))
        violations = svc.validate_pod_create({"gpu_count": 4})
        assert len(violations) == 1
        assert "exceeds maximum" in violations[0]

    def test_gpu_count_allowed(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_gpu_count=4))
        assert svc.validate_pod_create({"gpu_count": 2}) == []

    def test_gpu_count_default_one(self) -> None:
        """When gpu_count is not in params, default is 1."""
        svc = GuardrailsService(GuardrailsConfig(max_gpu_count=1))
        assert svc.validate_pod_create({}) == []

    def test_cpu_type_violation(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_cpu_types=["cpu3c-2-4"])
        )
        violations = svc.validate_pod_create(
            {"cpu_flavor_ids": ["cpu3c-8-16"]}
        )
        assert len(violations) == 1
        assert "cpu3c-8-16" in violations[0]

    def test_multiple_violations(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(
                allowed_gpu_types=["A100"],
                max_gpu_count=1,
            )
        )
        violations = svc.validate_pod_create(
            {"gpu_type_ids": ["H100"], "gpu_count": 4}
        )
        assert len(violations) == 2


# ---------------------------------------------------------------------------
# GuardrailsService — endpoint create
# ---------------------------------------------------------------------------


class TestValidateEndpointCreate:
    def test_endpoint_gpu_violation(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["AMPERE_24"])
        )
        violations = svc.validate_endpoint_create({"gpu_ids": "ADA_24"})
        assert len(violations) == 1
        assert "ADA_24" in violations[0]

    def test_endpoint_gpu_allowed(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["AMPERE_24"])
        )
        assert svc.validate_endpoint_create({"gpu_ids": "AMPERE_24"}) == []

    def test_endpoint_gpu_count_violation(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_gpu_count=1))
        violations = svc.validate_endpoint_create({"gpu_count": 4})
        assert len(violations) == 1

    def test_endpoint_no_gpu_ids(self) -> None:
        svc = GuardrailsService(
            GuardrailsConfig(allowed_gpu_types=["AMPERE_24"])
        )
        assert svc.validate_endpoint_create({}) == []


# ---------------------------------------------------------------------------
# GuardrailsService — spend limit
# ---------------------------------------------------------------------------


class TestCheckSpendLimit:
    def test_spend_over_limit(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_hourly_spend=1.00))
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 1.50, "clientBalance": 10.0}
        )
        assert len(warnings) == 1
        assert "meets or exceeds" in warnings[0]

    def test_spend_at_limit(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_hourly_spend=1.00))
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 1.00, "clientBalance": 10.0}
        )
        assert len(warnings) == 1

    def test_spend_under_limit(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_hourly_spend=5.00))
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 0.50, "clientBalance": 10.0}
        )
        assert warnings == []

    def test_zero_balance_warning(self) -> None:
        svc = GuardrailsService(GuardrailsConfig(max_hourly_spend=5.00))
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 0.10, "clientBalance": 0}
        )
        assert len(warnings) == 1
        assert "balance" in warnings[0].lower()

    def test_negative_balance_warning(self) -> None:
        svc = GuardrailsService(GuardrailsConfig())
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 0.10, "clientBalance": -5.0}
        )
        assert len(warnings) == 1
        assert "$-5.00" in warnings[0]

    def test_no_spend_limit_still_checks_balance(self) -> None:
        """Even without max_hourly_spend, zero balance is warned."""
        svc = GuardrailsService(GuardrailsConfig())
        warnings = svc.check_spend_limit(
            {"currentSpendPerHr": 0.10, "clientBalance": 0}
        )
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Settings integration
# ---------------------------------------------------------------------------


class TestSettingsGuardrails:
    def test_settings_guardrails_empty(self, tmp_config: object) -> None:
        from rpctl.config.settings import Settings

        settings = Settings.load(config_path=tmp_config)  # type: ignore[arg-type]
        gr = settings.guardrails
        assert gr.is_empty()

    def test_settings_guardrails_loaded(self, tmp_path: object) -> None:
        from pathlib import Path

        import yaml

        from rpctl.config.settings import Settings

        p = Path(str(tmp_path)) / "config.yaml"
        p.write_text(
            yaml.dump(
                {
                    "version": 1,
                    "active_profile": "default",
                    "defaults": {"cloud_type": "secure"},
                    "profiles": {"default": {"cloud_type": "secure"}},
                    "guardrails": {
                        "allowed_gpu_types": ["A100"],
                        "max_gpu_count": 2,
                    },
                }
            )
        )
        settings = Settings.load(config_path=p)
        gr = settings.guardrails
        assert gr.allowed_gpu_types == ["A100"]
        assert gr.max_gpu_count == 2

    def test_settings_set_guardrail(self, tmp_config: object) -> None:
        from rpctl.config.settings import Settings

        settings = Settings.load(config_path=tmp_config)  # type: ignore[arg-type]
        settings.set_guardrail("max_gpu_count", 4)
        assert settings._data["guardrails"]["max_gpu_count"] == 4

    def test_settings_set_guardrail_roundtrip(self, tmp_config: object) -> None:
        from rpctl.config.settings import Settings

        settings = Settings.load(config_path=tmp_config)  # type: ignore[arg-type]
        settings.set_guardrail("allowed_gpu_types", ["A100", "H100"])
        settings.save()

        reloaded = Settings.load(config_path=tmp_config)  # type: ignore[arg-type]
        gr = reloaded.guardrails
        assert gr.allowed_gpu_types == ["A100", "H100"]


# ---------------------------------------------------------------------------
# CLI commands — guardrails show / set-guardrail / clear-guardrail
# ---------------------------------------------------------------------------


class TestGuardrailsCLI:
    @patch("rpctl.cli.config.Settings.load")
    def test_guardrails_show_empty(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(data={"version": 1, "active_profile": "default"})
        mock_load.return_value = mock_settings

        result = runner.invoke(app, ["config", "guardrails"])
        assert result.exit_code == 0
        assert "No guardrails configured" in result.output

    @patch("rpctl.cli.config.Settings.load")
    def test_guardrails_show_with_values(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "guardrails": {
                    "allowed_gpu_types": ["A100", "H100"],
                    "max_gpu_count": 2,
                },
            }
        )
        mock_load.return_value = mock_settings

        result = runner.invoke(app, ["config", "guardrails"])
        assert result.exit_code == 0
        assert "A100" in result.output
        assert "H100" in result.output

    @patch("rpctl.cli.config.Settings.load")
    def test_set_guardrail_gpu_types(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={"version": 1, "active_profile": "default", "profiles": {}}
        )
        mock_settings.save = MagicMock()  # type: ignore[method-assign]
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app, ["config", "set-guardrail", "allowed_gpu_types", "A100,H100"]
        )
        assert result.exit_code == 0
        assert "Guardrail set" in result.output
        assert mock_settings._data["guardrails"]["allowed_gpu_types"] == [
            "A100",
            "H100",
        ]

    @patch("rpctl.cli.config.Settings.load")
    def test_set_guardrail_max_gpu_count(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={"version": 1, "active_profile": "default", "profiles": {}}
        )
        mock_settings.save = MagicMock()  # type: ignore[method-assign]
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app, ["config", "set-guardrail", "max_gpu_count", "4"]
        )
        assert result.exit_code == 0
        assert mock_settings._data["guardrails"]["max_gpu_count"] == 4

    @patch("rpctl.cli.config.Settings.load")
    def test_set_guardrail_max_hourly_spend(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={"version": 1, "active_profile": "default", "profiles": {}}
        )
        mock_settings.save = MagicMock()  # type: ignore[method-assign]
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app, ["config", "set-guardrail", "max_hourly_spend", "2.50"]
        )
        assert result.exit_code == 0
        assert mock_settings._data["guardrails"]["max_hourly_spend"] == 2.50

    def test_set_guardrail_invalid_key(self) -> None:
        with patch("rpctl.cli.config.Settings.load") as mock_load:
            from rpctl.config.settings import Settings

            mock_settings = Settings(
                data={"version": 1, "active_profile": "default", "profiles": {}}
            )
            mock_load.return_value = mock_settings

            result = runner.invoke(
                app, ["config", "set-guardrail", "bogus_key", "value"]
            )
            assert result.exit_code == 1
            assert "Invalid guardrail key" in result.output

    def test_set_guardrail_invalid_integer(self) -> None:
        with patch("rpctl.cli.config.Settings.load") as mock_load:
            from rpctl.config.settings import Settings

            mock_settings = Settings(
                data={"version": 1, "active_profile": "default", "profiles": {}}
            )
            mock_load.return_value = mock_settings

            result = runner.invoke(
                app, ["config", "set-guardrail", "max_gpu_count", "abc"]
            )
            assert result.exit_code == 1
            assert "not a valid integer" in result.output

    @patch("rpctl.cli.config.Settings.load")
    def test_clear_guardrail(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {},
                "guardrails": {"max_gpu_count": 4},
            }
        )
        mock_settings.save = MagicMock()  # type: ignore[method-assign]
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app, ["config", "clear-guardrail", "max_gpu_count"]
        )
        assert result.exit_code == 0
        assert "cleared" in result.output
        assert "max_gpu_count" not in mock_settings._data.get("guardrails", {})

    @patch("rpctl.cli.config.Settings.load")
    def test_clear_guardrail_not_set(self, mock_load: MagicMock) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {},
                "guardrails": {},
            }
        )
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app, ["config", "clear-guardrail", "max_gpu_count"]
        )
        assert result.exit_code == 0
        assert "was not set" in result.output


# ---------------------------------------------------------------------------
# CLI integration — pod create with guardrails
# ---------------------------------------------------------------------------


class TestPodCreateGuardrails:
    @patch("rpctl.cli.pod._get_pod_service")
    @patch("rpctl.config.settings.Settings.load")
    def test_pod_create_blocked_by_guardrail(
        self, mock_load: MagicMock, mock_svc: MagicMock
    ) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {"default": {"cloud_type": "secure"}},
                "guardrails": {"allowed_gpu_types": ["A100"]},
            }
        )
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "test",
                "--gpu",
                "H100",
            ],
        )
        assert result.exit_code == 7
        # The pod service create should NOT have been called
        mock_svc.return_value.create_pod.assert_not_called()

    @patch("rpctl.cli.pod._get_pod_service")
    @patch("rpctl.config.settings.Settings.load")
    def test_pod_create_force_bypasses_guardrail(
        self, mock_load: MagicMock, mock_svc: MagicMock
    ) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {"default": {"cloud_type": "secure"}},
                "guardrails": {"allowed_gpu_types": ["A100"]},
            }
        )
        mock_load.return_value = mock_settings

        # Mock the actual pod creation
        mock_svc.return_value.create_pod.return_value = MagicMock(
            id="pod-123",
            name="test",
            desired_status="RUNNING",
            image_name="test",
        )

        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "test",
                "--gpu",
                "H100",
                "--force",
            ],
        )
        # Should reach the create call (may fail for other reasons but not exit 7)
        assert result.exit_code != 7

    def test_pod_create_dry_run_skips_guardrails(self) -> None:
        """--dry-run should never trigger guardrails check."""
        result = runner.invoke(
            app,
            [
                "pod",
                "create",
                "--image",
                "test",
                "--gpu",
                "H100",
                "--dry-run",
            ],
        )
        # Dry run should succeed regardless of guardrails
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# CLI integration — endpoint create with guardrails
# ---------------------------------------------------------------------------


class TestEndpointCreateGuardrails:
    @patch("rpctl.cli.endpoint._get_endpoint_service")
    @patch("rpctl.config.settings.Settings.load")
    def test_endpoint_create_blocked_by_guardrail(
        self, mock_load: MagicMock, mock_svc: MagicMock
    ) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {"default": {"cloud_type": "secure"}},
                "guardrails": {"allowed_gpu_types": ["AMPERE_24"]},
            }
        )
        mock_load.return_value = mock_settings

        result = runner.invoke(
            app,
            [
                "endpoint",
                "create",
                "--name",
                "test-ep",
                "--template",
                "tmpl-123",
                "--gpu",
                "ADA_24",
            ],
        )
        assert result.exit_code == 7
        mock_svc.return_value.create_endpoint.assert_not_called()

    @patch("rpctl.cli.endpoint._get_endpoint_service")
    @patch("rpctl.config.settings.Settings.load")
    def test_endpoint_create_force_bypasses_guardrail(
        self, mock_load: MagicMock, mock_svc: MagicMock
    ) -> None:
        from rpctl.config.settings import Settings

        mock_settings = Settings(
            data={
                "version": 1,
                "active_profile": "default",
                "profiles": {"default": {"cloud_type": "secure"}},
                "guardrails": {"allowed_gpu_types": ["AMPERE_24"]},
            }
        )
        mock_load.return_value = mock_settings

        mock_svc.return_value.create_endpoint.return_value = MagicMock(
            id="ep-123", name="test-ep"
        )

        result = runner.invoke(
            app,
            [
                "endpoint",
                "create",
                "--name",
                "test-ep",
                "--template",
                "tmpl-123",
                "--gpu",
                "ADA_24",
                "--force",
            ],
        )
        assert result.exit_code != 7
