import json
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_json_output, set_active_profile


def fake_result(**kw):
    base = {"success": True, "error": None}
    base.update(kw)
    ns = SimpleNamespace(**base)
    ns.to_dict = lambda: {k: v for k, v in base.items() if v is not None}
    return ns


AUTH_OK = fake_result(message_id="am-1", invalid_staff=None, invalid_department=None, raw_response={"errCode": 0})


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


def run(args):
    return CliRunner().invoke(app, args)


def test_authorization_request_chat_id_success():
    mock_client = MagicMock()
    mock_client.send_authorization_request.return_value = AUTH_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "send-authorization-request", "--chat-id", "u1", "--yes"])
    assert result.exit_code == 0
    mock_client.send_authorization_request.assert_called_once_with(
        chat_ids=["u1"],
        department_ids=None,
        authorization_type=1,
        entry_id="",
        user_token="",
    )
    assert "授权请求结果" in result.stdout


def test_authorization_request_department_id_success():
    mock_client = MagicMock()
    mock_client.send_authorization_request.return_value = AUTH_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "send-authorization-request", "--department-id", "d1", "--yes"])
    assert result.exit_code == 0
    assert mock_client.send_authorization_request.call_args.kwargs["department_ids"] == ["d1"]
    assert mock_client.send_authorization_request.call_args.kwargs["chat_ids"] is None


def test_authorization_request_multiple_targets_and_flags():
    mock_client = MagicMock()
    mock_client.send_authorization_request.return_value = AUTH_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run([
            "message", "send-authorization-request",
            "--chat-id", "u1", "--chat-id", "u2",
            "--department-id", "d1",
            "--authorization-type", "1",
            "--entry-id", "entry-9",
            "--user-token", "ut-1",
            "--yes",
        ])
    assert result.exit_code == 0
    mock_client.send_authorization_request.assert_called_once_with(
        chat_ids=["u1", "u2"],
        department_ids=["d1"],
        authorization_type=1,
        entry_id="entry-9",
        user_token="ut-1",
    )


def test_authorization_request_missing_targets_exits_1():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "send-authorization-request", "--yes"])
    assert result.exit_code == 1
    assert "错误" in result.stdout
    assert "--chat-id" in result.stdout
    assert "--department-id" in result.stdout
    gc.assert_not_called()


def test_authorization_request_missing_targets_json_error_shape():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "send-authorization-request", "--yes"])
    assert result.exit_code == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_parameter"
    gc.assert_not_called()


def test_authorization_request_json_shape():
    mock_client = MagicMock()
    mock_client.send_authorization_request.return_value = AUTH_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["--json", "message", "send-authorization-request", "--chat-id", "u1", "--yes"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["message_id"] == "am-1"


def test_authorization_request_failure_exits_1():
    mock_client = MagicMock()
    mock_client.send_authorization_request.return_value = fake_result(success=False, error="boom")
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "send-authorization-request", "--chat-id", "u1", "--yes"])
    assert result.exit_code == 1
    assert "boom" in result.stdout


def test_authorization_request_without_yes_exits_10():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "send-authorization-request", "--chat-id", "u1"])
    assert result.exit_code == 10
    assert "Confirmation required" in result.stdout
    gc.assert_not_called()


def test_authorization_request_json_without_yes_exit10_envelope():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "send-authorization-request", "--department-id", "d1"])
    assert result.exit_code == 10
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "confirmation_required"
    assert payload["error"]["risk"]["level"] == "high-risk-write"
    assert payload["error"]["risk"]["action"] == "send authorization request to d1"
    gc.assert_not_called()


def test_authorization_request_dry_run_exits_0_no_call():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "send-authorization-request", "--chat-id", "u1", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout
    gc.assert_not_called()


def test_authorization_request_dry_run_json_shape():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "send-authorization-request", "--chat-id", "u1", "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["would_perform"] == "send authorization request to u1"
    gc.assert_not_called()
