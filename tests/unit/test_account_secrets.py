"""Unit tests for account info, secrets — RestClient, services, CLI, and query builders."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rpctl.errors import RpctlError
from rpctl.main import app

runner = CliRunner()


# --- Fixtures ---


@pytest.fixture
def client():
    """Create a RestClient with a mocked GraphQL client."""
    from rpctl.api.rest_client import RestClient

    c = RestClient.__new__(RestClient)
    c._api_key = "test-key"
    c._gql = MagicMock()
    return c


def _mock_settings():
    mock = MagicMock()
    mock.api_key = "test-key"
    mock.active_profile = "default"
    return mock


# --- RestClient methods ---


class TestRestClientAccount:
    """Tests for RestClient account/secret methods."""

    def test_get_account_info(self, client):
        """get_account_info calls GraphQL and returns myself dict."""
        client._gql.execute.return_value = {
            "myself": {"clientBalance": 50.0, "currentSpendPerHr": 1.23, "spendLimit": 100.0},
        }
        result = client.get_account_info()
        assert result == {"clientBalance": 50.0, "currentSpendPerHr": 1.23, "spendLimit": 100.0}
        client._gql.execute.assert_called_once()

    def test_get_secrets(self, client):
        """get_secrets returns list of secrets from myself.secrets."""
        client._gql.execute.return_value = {
            "myself": {"secrets": [{"name": "API_TOKEN", "value": "abc123"}]},
        }
        result = client.get_secrets()
        assert result == [{"name": "API_TOKEN", "value": "abc123"}]
        client._gql.execute.assert_called_once()

    def test_add_secret(self, client):
        """add_secret builds mutation with name/value and executes."""
        client._gql.execute.return_value = {"addSecret": None}
        result = client.add_secret("MY_KEY", "my_value")
        assert result == {"addSecret": None}
        call_args = client._gql.execute.call_args[0][0]
        assert "addSecret" in call_args
        assert "MY_KEY" in call_args
        assert "my_value" in call_args

    def test_delete_secret(self, client):
        """delete_secret builds delete mutation and executes."""
        client._gql.execute.return_value = {"deleteSecret": None}
        result = client.delete_secret("MY_KEY")
        assert result == {"deleteSecret": None}
        call_args = client._gql.execute.call_args[0][0]
        assert "deleteSecret" in call_args
        assert "MY_KEY" in call_args

    def test_add_secret_escapes_quotes(self, client):
        """add_secret escapes double quotes in values."""
        client._gql.execute.return_value = {"addSecret": None}
        client.add_secret("KEY", 'value with "quotes"')
        call_args = client._gql.execute.call_args[0][0]
        assert '\\"quotes\\"' in call_args


# --- SecretService ---


class TestSecretService:
    """Tests for SecretService delegation."""

    def test_list_secrets(self):
        """list_secrets delegates to client.get_secrets."""
        from rpctl.services.secret_service import SecretService

        mock_client = MagicMock()
        mock_client.get_secrets.return_value = [{"name": "S1", "value": "v1"}]
        svc = SecretService(mock_client)
        result = svc.list_secrets()
        assert result == [{"name": "S1", "value": "v1"}]
        mock_client.get_secrets.assert_called_once()

    def test_set_secret(self):
        """set_secret delegates to client.add_secret."""
        from rpctl.services.secret_service import SecretService

        mock_client = MagicMock()
        mock_client.add_secret.return_value = {"addSecret": None}
        svc = SecretService(mock_client)
        result = svc.set_secret("KEY", "VAL")
        assert result == {"addSecret": None}
        mock_client.add_secret.assert_called_once_with("KEY", "VAL")

    def test_delete_secret(self):
        """delete_secret delegates to client.delete_secret."""
        from rpctl.services.secret_service import SecretService

        mock_client = MagicMock()
        mock_client.delete_secret.return_value = {"deleteSecret": None}
        svc = SecretService(mock_client)
        result = svc.delete_secret("KEY")
        assert result == {"deleteSecret": None}
        mock_client.delete_secret.assert_called_once_with("KEY")


# --- UserService ---


class TestUserService:
    """Tests for UserService delegation."""

    def test_get_account_info(self):
        """get_account_info delegates to client.get_account_info."""
        from rpctl.services.user_service import UserService

        mock_client = MagicMock()
        mock_client.get_account_info.return_value = {
            "clientBalance": 50.0,
            "currentSpendPerHr": 1.0,
            "spendLimit": 100.0,
        }
        svc = UserService(mock_client)
        result = svc.get_account_info()
        assert result["clientBalance"] == 50.0
        mock_client.get_account_info.assert_called_once()


# --- CLI commands ---


class TestUserCLI:
    """Tests for user balance and spending CLI commands."""

    def test_user_balance_command(self):
        """'user balance' invokes service and outputs balance info."""
        with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.get_account_info.return_value = {
                "clientBalance": 42.50,
                "currentSpendPerHr": 0.75,
                "spendLimit": 200.0,
            }
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["user", "balance"])
            assert result.exit_code == 0
            mock_svc.get_account_info.assert_called_once()

    def test_user_spending_command(self):
        """'user spending' invokes service and outputs spending info."""
        with patch("rpctl.cli.user._get_user_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.get_account_info.return_value = {
                "clientBalance": 42.50,
                "currentSpendPerHr": 0.75,
                "spendLimit": 200.0,
            }
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["user", "spending"])
            assert result.exit_code == 0
            mock_svc.get_account_info.assert_called_once()


class TestSecretCLI:
    """Tests for secret CRUD CLI commands."""

    def test_secret_list_command(self):
        """'secret list' masks secret values by default."""
        with patch("rpctl.cli.secret._get_secret_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.list_secrets.return_value = [
                {"name": "TOKEN", "value": "supersecret"},
            ]
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["secret", "list"])
            assert result.exit_code == 0
            # Value should be masked
            assert "supersecret" not in result.output

    def test_secret_list_reveal(self):
        """'secret list --reveal' shows actual values."""
        with patch("rpctl.cli.secret._get_secret_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.list_secrets.return_value = [
                {"name": "TOKEN", "value": "supersecret"},
            ]
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["secret", "list", "--reveal"])
            assert result.exit_code == 0
            mock_svc.list_secrets.assert_called_once()

    def test_secret_set_command(self):
        """'secret set NAME VALUE' calls service and shows success."""
        with patch("rpctl.cli.secret._get_secret_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.set_secret.return_value = {"addSecret": None}
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["secret", "set", "MY_KEY", "my_value"])
            assert result.exit_code == 0
            assert "MY_KEY" in result.output
            mock_svc.set_secret.assert_called_once_with("MY_KEY", "my_value")

    def test_secret_delete_command(self):
        """'secret delete NAME' calls service and shows success."""
        with patch("rpctl.cli.secret._get_secret_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.delete_secret.return_value = {"deleteSecret": None}
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["secret", "delete", "MY_KEY"])
            assert result.exit_code == 0
            assert "MY_KEY" in result.output
            mock_svc.delete_secret.assert_called_once_with("MY_KEY")

    def test_secret_list_error(self):
        """'secret list' handles API errors gracefully."""
        with patch("rpctl.cli.secret._get_secret_service") as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.list_secrets.side_effect = RpctlError("API failure")
            mock_svc_fn.return_value = mock_svc

            result = runner.invoke(app, ["secret", "list"])
            assert result.exit_code == 1


# --- GraphQL query builders ---


class TestQueryBuilders:
    """Tests for secret-related GraphQL query builder functions."""

    def test_build_add_secret_mutation(self):
        """build_add_secret_mutation generates correct mutation string."""
        from rpctl.api.queries import build_add_secret_mutation

        query = build_add_secret_mutation("MY_SECRET", "secret_value")
        assert "addSecret" in query
        assert "MY_SECRET" in query
        assert "secret_value" in query
        assert "mutation" in query

    def test_build_delete_secret_mutation(self):
        """build_delete_secret_mutation generates correct mutation string."""
        from rpctl.api.queries import build_delete_secret_mutation

        query = build_delete_secret_mutation("MY_SECRET")
        assert "deleteSecret" in query
        assert "MY_SECRET" in query
        assert "mutation" in query

    def test_build_add_secret_escapes_quotes(self):
        """build_add_secret_mutation escapes double quotes in name and value."""
        from rpctl.api.queries import build_add_secret_mutation

        query = build_add_secret_mutation('key"name', 'val"ue')
        assert '\\"' in query
        # Should not contain unescaped quotes that would break the mutation
        # The escaped quotes should be present
        assert 'key\\"name' in query
        assert 'val\\"ue' in query
