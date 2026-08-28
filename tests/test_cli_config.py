import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_sdk import CredentialStore as _RealCredentialStore

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


# ── identity_type persistence (real store, isolated state file) ──


@pytest.fixture
def isolated_store(tmp_path):
    """Patch config.py's CredentialStore to use a real store on a temp state file."""
    state_path = str(tmp_path / "sdk_state.json")

    def factory(path=None, profile="default"):
        return _RealCredentialStore(path=state_path, profile=profile)

    with patch("lansenger_cli.commands.config.CredentialStore", side_effect=factory):
        yield state_path


def test_config_set_identity_type_round_trip(isolated_store):
    """`config set identity_type personal-bot` persists; `config show` displays it."""
    runner = CliRunner()
    result = runner.invoke(app, ["config", "set", "identity_type", "personal-bot"])
    assert result.exit_code == 0
    assert "personal-bot" in result.stdout

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "identity_type: personal-bot" in result.stdout


def test_config_set_identity_type_invalid_value(isolated_store):
    """`config set identity_type bad-value` exits non-zero with an error."""
    runner = CliRunner()
    result = runner.invoke(app, ["config", "set", "identity_type", "bad-value"])
    assert result.exit_code != 0
    assert "Invalid identity_type" in result.stdout

    store = _RealCredentialStore(path=isolated_store, profile="default")
    assert store.load_identity_type() == ""


def test_config_set_identity_type_empty_string_clears(isolated_store):
    """`config set identity_type ""` clears the stored identity type."""
    runner = CliRunner()
    assert runner.invoke(app, ["config", "set", "identity_type", "org-app"]).exit_code == 0

    result = runner.invoke(app, ["config", "set", "identity_type", ""])
    assert result.exit_code == 0
    assert "(cleared)" in result.stdout

    store = _RealCredentialStore(path=isolated_store, profile="default")
    assert store.load_identity_type() == ""

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "identity_type: org-app" not in result.stdout


def test_config_list_profiles_shows_identity_type(isolated_store):
    """`config list-profiles` shows the stored identity type."""
    runner = CliRunner()
    assert runner.invoke(app, ["config", "set", "identity_type", "org-bot"]).exit_code == 0

    result = runner.invoke(app, ["config", "list-profiles"])
    assert result.exit_code == 0
    assert "type=org-bot" in result.stdout


def test_config_set_other_key_preserves_identity_type(isolated_store):
    """Setting another config key does not wipe the stored identity type."""
    runner = CliRunner()
    assert runner.invoke(app, ["config", "set", "identity_type", "personal-bot"]).exit_code == 0
    assert runner.invoke(app, ["config", "set", "app_id", "app-123"]).exit_code == 0

    store = _RealCredentialStore(path=isolated_store, profile="default")
    creds = store.load_credentials()
    assert creds["app_id"] == "app-123"
    assert creds["identity_type"] == "personal-bot"

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "identity_type: personal-bot" in result.stdout
