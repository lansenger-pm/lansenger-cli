import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_json_output, set_active_profile


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


# --- exit 10 gate (no --yes) ---

def test_dismiss_without_yes_exits_10():
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client") as gc:
        result = runner.invoke(app, ["group", "dismiss", "g1"])
    assert result.exit_code == 10
    assert "Confirmation required" in result.stdout
    gc.assert_not_called()  # no API call without --yes


def test_dismiss_with_yes_calls_client():
    mock_client = MagicMock()
    mock_client.dismiss_group.return_value.success = True
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client", return_value=mock_client):
        result = runner.invoke(app, ["group", "dismiss", "g1", "--yes"])
    assert result.exit_code == 0
    mock_client.dismiss_group.assert_called_once()


def test_revoke_without_yes_exits_10():
    runner = CliRunner()
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(app, ["message", "revoke", "m1"])
    assert result.exit_code == 10
    gc.assert_not_called()


def test_update_members_add_only_no_gate():
    """Adding members (no --remove) is not high-risk, no --yes needed."""
    mock_client = MagicMock()
    mock_client.update_group_members.return_value.success = True
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client", return_value=mock_client):
        result = runner.invoke(app, ["group", "update-members", "g1", "--add", "u1"])
    assert result.exit_code == 0
    mock_client.update_group_members.assert_called_once()


def test_update_members_remove_requires_yes():
    mock_client = MagicMock()
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client", return_value=mock_client):
        result = runner.invoke(app, ["group", "update-members", "g1", "--remove", "u1"])
    assert result.exit_code == 10
    mock_client.update_group_members.assert_not_called()


def test_todo_delete_without_yes_exits_10():
    runner = CliRunner()
    with patch("lansenger_cli.commands.todo.get_client") as gc:
        result = runner.invoke(app, ["todo", "delete", "t1", "org1"])
    assert result.exit_code == 10
    gc.assert_not_called()


def test_calendar_delete_schedule_without_yes_exits_10():
    runner = CliRunner()
    with patch("lansenger_cli.commands.calendar.get_client") as gc:
        result = runner.invoke(app, ["calendar", "delete-schedule", "cal1", "sch1"])
    assert result.exit_code == 10
    gc.assert_not_called()


# --- structured JSON on exit 10 ---

def test_dismiss_json_exit10_envelope():
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client") as gc:
        result = runner.invoke(app, ["--json", "group", "dismiss", "g1"])
    assert result.exit_code == 10
    # structured payload goes to stderr in JSON mode
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "confirmation_required"
    assert payload["error"]["risk"]["level"] == "high-risk-write"
    assert payload["error"]["risk"]["action"] == "dismiss group g1"
    gc.assert_not_called()


# --- dry-run ---

def test_dismiss_dry_run_exits_0_no_call():
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client") as gc:
        result = runner.invoke(app, ["group", "dismiss", "g1", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout
    gc.assert_not_called()


def test_dismiss_dry_run_json():
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client") as gc:
        result = runner.invoke(app, ["--json", "group", "dismiss", "g1", "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["would_perform"] == "dismiss group g1"
    gc.assert_not_called()


def test_update_members_remove_dry_run_json():
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client") as gc:
        result = runner.invoke(
            app, ["--json", "group", "update-members", "g1", "--remove", "u1,u2", "--dry-run"]
        )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert "remove members" in payload["would_perform"]
    gc.assert_not_called()


# --- JSON mode failure exit code (was bug: returned 0) ---

class _FakeResult:
    """Minimal stand-in for an SDK result object (no auto-created attrs)."""
    def __init__(self, success, error="", retryable=False, message_id=None, operation=None):
        self.success = success
        self.error = error
        self.retryable = retryable
        self.message_id = message_id
        self.operation = operation

    def to_dict(self):
        d = {"success": self.success}
        if self.error:
            d["error"] = self.error
        if self.message_id is not None:
            d["message_id"] = self.message_id
        return d


def test_json_mode_failure_exits_nonzero():
    """A failed API result must exit non-zero even in --json mode."""
    mock_client = MagicMock()
    mock_client.dismiss_group.return_value = _FakeResult(success=False, error="boom")
    runner = CliRunner()
    with patch("lansenger_cli.commands.group.get_client", return_value=mock_client):
        result = runner.invoke(app, ["--json", "group", "dismiss", "g1", "--yes"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"] == "boom"
