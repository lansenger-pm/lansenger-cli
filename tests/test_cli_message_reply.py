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


REPLY_OK = fake_result(reply_type=1, msg_id="m1", emoji_id="TYPE_OK", raw_response={"errCode": 0})
REPLY_CANCELLED = fake_result(reply_type=2, msg_id="m1", emoji_id="")


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


def run(args):
    return CliRunner().invoke(app, args)


def test_reply_success_calls_sdk():
    mock_client = MagicMock()
    mock_client.reply_message.return_value = REPLY_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "reply", "m1", "--emoji", "TYPE_OK", "--yes"])
    assert result.exit_code == 0
    mock_client.reply_message.assert_called_once_with(
        msg_id="m1", emoji_id="TYPE_OK", reply_type=1, user_token=""
    )
    assert "回复消息结果" in result.stdout


def test_reply_cancel_uses_reply_type_2():
    mock_client = MagicMock()
    mock_client.reply_message.return_value = REPLY_CANCELLED
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "reply", "m1", "--cancel", "--yes"])
    assert result.exit_code == 0
    mock_client.reply_message.assert_called_once_with(
        msg_id="m1", emoji_id="", reply_type=2, user_token=""
    )


def test_reply_passes_user_token():
    mock_client = MagicMock()
    mock_client.reply_message.return_value = REPLY_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "reply", "m1", "--emoji", "TYPE_LOVE", "--user-token", "ut-1", "--yes"])
    assert result.exit_code == 0
    mock_client.reply_message.assert_called_once_with(
        msg_id="m1", emoji_id="TYPE_LOVE", reply_type=1, user_token="ut-1"
    )


@pytest.mark.parametrize("bad", ["TYPE_NOPE", "TYPE_OK ", "ok"])
def test_reply_invalid_emoji_exits_1_with_chinese_error(bad):
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--emoji", bad, "--yes"])
    assert result.exit_code == 1
    assert "错误" in result.stdout
    assert "表情类型非法" in result.stdout
    gc.assert_not_called()


def test_reply_requires_emoji_or_cancel():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--yes"])
    assert result.exit_code == 1
    assert "错误" in result.stdout
    gc.assert_not_called()


def test_reply_cancel_conflicts_with_emoji():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--cancel", "--emoji", "TYPE_OK", "--yes"])
    assert result.exit_code == 1
    assert "互斥" in result.stdout
    gc.assert_not_called()


def test_reply_invalid_emoji_json_error_shape():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "reply", "m1", "--emoji", "TYPE_NOPE", "--yes"])
    assert result.exit_code == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_parameter"
    gc.assert_not_called()


def test_reply_json_shape():
    mock_client = MagicMock()
    mock_client.reply_message.return_value = REPLY_OK
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["--json", "message", "reply", "m1", "--emoji", "TYPE_OK", "--yes"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["reply_type"] == 1
    assert payload["msg_id"] == "m1"
    assert payload["emoji_id"] == "TYPE_OK"


def test_reply_failure_exits_1():
    mock_client = MagicMock()
    mock_client.reply_message.return_value = fake_result(success=False, error="boom")
    with patch("lansenger_cli.commands.message.get_client", return_value=mock_client):
        result = run(["message", "reply", "m1", "--emoji", "TYPE_OK", "--yes"])
    assert result.exit_code == 1
    assert "boom" in result.stdout


def test_reply_without_yes_exits_10():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--emoji", "TYPE_OK"])
    assert result.exit_code == 10
    assert "Confirmation required" in result.stdout
    gc.assert_not_called()


def test_reply_json_without_yes_exit10_envelope():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "reply", "m1", "--emoji", "TYPE_OK"])
    assert result.exit_code == 10
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "confirmation_required"
    assert payload["error"]["risk"]["level"] == "high-risk-write"
    assert payload["error"]["risk"]["action"] == "reply message m1"
    gc.assert_not_called()


def test_reply_cancel_without_yes_exits_10():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--cancel"])
    assert result.exit_code == 10
    gc.assert_not_called()


def test_reply_dry_run_exits_0_no_call():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["message", "reply", "m1", "--emoji", "TYPE_OK", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout
    gc.assert_not_called()


def test_reply_dry_run_json_shape():
    with patch("lansenger_cli.commands.message.get_client") as gc:
        result = run(["--json", "message", "reply", "m1", "--emoji", "TYPE_OK", "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["would_perform"] == "reply message m1"
    gc.assert_not_called()
