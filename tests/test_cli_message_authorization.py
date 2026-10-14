"""Tests for `lansenger message send-authorization-request` (SDK 4.6.4.14)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_active_profile, set_json_output


class _FakeAccountMessageResult:
    def __init__(self, success=True, message_id="am-1", invalid_staff=None, invalid_department=None, error=None):
        self.success = success
        self.message_id = message_id
        self.invalid_staff = invalid_staff
        self.invalid_department = invalid_department
        self.error = error

    def to_dict(self):
        d = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.invalid_staff is not None:
            d["invalid_staff"] = self.invalid_staff
        if self.invalid_department is not None:
            d["invalid_department"] = self.invalid_department
        if self.error is not None:
            d["error"] = self.error
        return d


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


runner = CliRunner()


def test_authorization_request_passes_all_kwargs():
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult()
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(
            app,
            [
                "message", "send-authorization-request", "u1",
                "--type", "1", "--ref-msg-id", "m-9",
            ],
        )
    assert result.exit_code == 0, result.output
    client.send_authorization_request.assert_called_once_with(
        chat_id="u1",
        authorization_type=1,
        ref_msg_id="m-9",
    )
    assert "授权请求结果" in result.output


def test_authorization_request_defaults_match_sdk_signature():
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult()
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "send-authorization-request", "u1"])
    assert result.exit_code == 0, result.output
    client.send_authorization_request.assert_called_once_with(
        chat_id="u1",
        authorization_type=1,
        ref_msg_id="",
    )


def test_authorization_request_requires_a_receiver():
    """The msgType only supports bot -> staff private chat, so a chatId is mandatory."""
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(app, ["message", "send-authorization-request"])
    assert result.exit_code != 0
    gc.assert_not_called()


def test_authorization_request_is_not_gated_like_send_account_message():
    """Mirrors `message send-account-message`: no --yes, no exit 10, API called directly."""
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult()
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "send-authorization-request", "u1"])
    assert result.exit_code == 0, result.output
    assert "Confirmation required" not in result.output
    client.send_authorization_request.assert_called_once()


@pytest.mark.parametrize("bad", ["0", "2", "9"])
def test_authorization_request_rejects_other_authorization_types(bad):
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(
            app, ["message", "send-authorization-request", "u1", "--type", bad]
        )
    assert result.exit_code == 1
    assert "授权类型" in result.output
    gc.assert_not_called()


def test_authorization_request_accepts_authorization_type_alias():
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult()
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(
            app,
            ["message", "send-authorization-request", "u1", "--authorization-type", "1"],
        )
    assert result.exit_code == 0, result.output
    assert client.send_authorization_request.call_args.kwargs["authorization_type"] == 1


def test_authorization_request_failure_exits_1():
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult(
        success=False, message_id=None, error="boom"
    )
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "send-authorization-request", "u1"])
    assert result.exit_code == 1
    assert "boom" in result.output


def test_authorization_request_json_shape():
    client = MagicMock()
    client.send_authorization_request.return_value = _FakeAccountMessageResult()
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(
            app, ["--json", "message", "send-authorization-request", "u1"]
        )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["message_id"] == "am-1"


def test_authorization_request_json_param_error_keeps_stdout_clean():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(
            app, ["--json", "message", "send-authorization-request", "u1", "--type", "2"]
        )
    assert result.exit_code == 1
    assert result.stdout.strip() == ""
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_parameter"
    gc.assert_not_called()
