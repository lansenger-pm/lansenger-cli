import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_json_output, set_active_profile


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset global state between tests to avoid cross-test interference."""
    set_json_output(False)
    set_active_profile("default")


def test_config_show_basic():
    """`lansenger config show` displays profile info."""
    mock_store = MagicMock()
    mock_store.load_credentials.return_value = {
        "app_id": "test-app-id",
        "app_secret": "test-secret",
        "api_gateway_url": "https://api.example.com",
        "passport_url": "",
        "redirect_uri": "",
        "encoding_key": "",
        "callback_token": "",
    }
    mock_store.has_credentials.return_value = True
    mock_store.has_full_config.return_value = True
    mock_store.path = "/tmp/fake-store.json"

    with patch("lansenger_cli.commands.config.CredentialStore", return_value=mock_store):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "Profile: default" in result.stdout
    assert "Credentials configured: True" in result.stdout
    assert "Store path: /tmp/fake-store.json" in result.stdout


def test_config_show_json():
    """`lansenger config show --json` outputs masked data."""
    mock_store = MagicMock()
    mock_store.load.return_value = {
        "profiles": {
            "default": {
                "app_id": "test-app-id",
                "app_secret": "sensitive-secret",
                "api_gateway_url": "https://api.example.com",
            }
        }
    }

    with patch("lansenger_cli.commands.config.CredentialStore", return_value=mock_store):
        runner = CliRunner()
        result = runner.invoke(app, ["--json", "config", "show"])

    assert result.exit_code == 0
    # app_id is visible, secret is masked
    assert "test-app-id" in result.stdout
    assert "***" in result.stdout
    assert "sensitive-secret" not in result.stdout


def test_config_list_profiles():
    """`lansenger config list-profiles` lists available profiles."""
    mock_store = MagicMock()
    mock_store.list_profiles.return_value = ["default", "dev", "staging"]
    mock_store.get_active_profile.return_value = "default"
    mock_store.load_credentials.return_value = {
        "app_id": "test-app",
        "api_gateway_url": "https://api.example.com",
    }
    mock_store.has_credentials.return_value = True

    with patch("lansenger_cli.commands.config.CredentialStore", return_value=mock_store):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "list-profiles"])

    assert result.exit_code == 0
    assert "Active profile: default" in result.stdout
    assert "default" in result.stdout
    assert "dev" in result.stdout
    assert "staging" in result.stdout
    assert "test-app" in result.stdout


def test_config_show_with_explicit_profile():
    """`lansenger config show --profile dev` uses the specified profile."""
    mock_store = MagicMock()
    mock_store.load_credentials.return_value = {
        "app_id": "dev-app-id",
        "app_secret": "",
        "api_gateway_url": "",
        "passport_url": "",
        "redirect_uri": "",
        "encoding_key": "",
        "callback_token": "",
    }
    mock_store.has_credentials.return_value = True
    mock_store.has_full_config.return_value = False
    mock_store.path = "/tmp/dev-store.json"

    with patch("lansenger_cli.commands.config.CredentialStore", return_value=mock_store):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "show", "--profile", "dev"])

    assert result.exit_code == 0
    assert "Profile: dev" in result.stdout
    assert "Full config available: False" in result.stdout
