"""Tests for `lansenger message reply` — emoji reply / cancel (SDK 4.6.17)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_active_profile, set_json_output


class _FakeReplyResult:
    def __init__(self, success=True, reply_type=1, msg_id="m-1", emoji_id="", error=None):
        self.success = success
        self.reply_type = reply_type
        self.msg_id = msg_id
        self.emoji_id = emoji_id
        self.error = error

    def to_dict(self):
        d = {"success": self.success}
        if self.reply_type:
            d["reply_type"] = self.reply_type
        if self.msg_id:
            d["msg_id"] = self.msg_id
        if self.emoji_id:
            d["emoji_id"] = self.emoji_id
        if self.error is not None:
            d["error"] = self.error
        return d


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


runner = CliRunner()


def test_reply_success_calls_client_with_kwargs():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(emoji_id="TYPE_THUMB")
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "reply", "m-1", "--emoji", "TYPE_THUMB"])
    assert result.exit_code == 0, result.output
    client.reply_message.assert_called_once_with(
        msg_id="m-1", emoji_id="TYPE_THUMB", reply_type=1, user_token=""
    )
    assert "表情回复" in result.output


def test_reply_cancel_sets_reply_type_2_without_emoji():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(reply_type=2)
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "reply", "m-1", "--cancel"])
    assert result.exit_code == 0, result.output
    client.reply_message.assert_called_once_with(
        msg_id="m-1", emoji_id="", reply_type=2, user_token=""
    )


def test_reply_passes_user_token():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(emoji_id="TYPE_LOVE")
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(
            app, ["message", "reply", "m-1", "--emoji", "TYPE_LOVE", "--user-token", "ut-1"]
        )
    assert result.exit_code == 0, result.output
    client.reply_message.assert_called_once_with(
        msg_id="m-1", emoji_id="TYPE_LOVE", reply_type=1, user_token="ut-1"
    )


def test_reply_is_not_high_risk_no_yes_needed():
    """Emoji replies are reversible, so the command must not sit behind confirm_high_risk."""
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(emoji_id="TYPE_OK")
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "reply", "m-1", "--emoji", "TYPE_OK"])
    assert result.exit_code == 0, result.output
    assert "Confirmation required" not in result.output


@pytest.mark.parametrize("bad", ["TYPE_NOPE", "type_ok", "LOVE", "1"])
def test_reply_invalid_emoji_exits_1_with_chinese_error(bad):
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(app, ["message", "reply", "m-1", "--emoji", bad])
    assert result.exit_code == 1
    assert "错误" in result.output
    assert "表情类型非法" in result.output
    gc.assert_not_called()


def test_reply_without_emoji_and_without_cancel_exits_1():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(app, ["message", "reply", "m-1"])
    assert result.exit_code == 1
    assert "必须指定" in result.output
    gc.assert_not_called()


def test_reply_each_documented_emoji_is_accepted():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(emoji_id="TYPE_ADD_ONE")
    for emoji in ("TYPE_THUMB", "TYPE_OK", "TYPE_ADD_ONE", "TYPE_FIREWORK", "TYPE_LOVE", "TYPE_DOUBT"):
        with patch("lansenger_cli.commands.message.get_client", return_value=client):
            result = runner.invoke(app, ["message", "reply", "m-1", "--emoji", emoji])
        assert result.exit_code == 0, (emoji, result.output)


def test_reply_failure_exits_1():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(success=False, error="boom")
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["message", "reply", "m-1", "--emoji", "TYPE_OK"])
    assert result.exit_code == 1
    assert "boom" in result.output


def test_reply_json_success_is_pure_json_on_stdout():
    client = MagicMock()
    client.reply_message.return_value = _FakeReplyResult(emoji_id="TYPE_OK")
    with patch("lansenger_cli.commands.message.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "message", "reply", "m-1", "--emoji", "TYPE_OK"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload == {
        "success": True,
        "reply_type": 1,
        "msg_id": "m-1",
        "emoji_id": "TYPE_OK",
    }


def test_reply_json_param_error_keeps_stdout_clean():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = runner.invoke(app, ["--json", "message", "reply", "m-1", "--emoji", "TYPE_NOPE"])
    assert result.exit_code == 1
    assert result.stdout.strip() == ""
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_parameter"
    gc.assert_not_called()
