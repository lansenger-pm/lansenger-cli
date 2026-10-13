import json
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.commands import oauth as oauth_mod
from lansenger_cli.utils import set_json_output, set_active_profile


def fake_result(**kw):
    base = {"success": True, "error": None, "error_type": None}
    base.update(kw)
    ns = SimpleNamespace(**base)
    ns.to_dict = lambda: {k: v for k, v in base.items() if v is not None}
    return ns


AUTH_OK = fake_result(
    device_code="d" * 40,
    user_code="WDJB-MJHT",
    verification_uri_complete="https://pp.example.com/oauth/device_verify?user_code=WDJB-MJHT",
    interval=5,
    expires_in=600,
    expires_at=1791864291,
    open_api_domain="https://gw.example.com",
)

POLL_PENDING = fake_result(state="authorization_pending", oauth2_code=None)
POLL_APPROVED = fake_result(state="access_approved", oauth2_code="c" * 36)
POLL_DENIED = fake_result(success=False, state="access_denied", oauth2_code=None)
POLL_EXPIRED = fake_result(success=False, state="expired_token", oauth2_code=None)
EXCHANGE_OK = fake_result(
    user_token="u" * 36,
    expires_in=7200,
    refresh_token="r" * 36,
    refresh_expires_in=2592000,
    staff_id="staff-001",
    scope="basic_userinfor",
)

UNSUPPORTED = fake_result(success=False, error="deviceflow unavailable (HTTP 404)", error_type="deviceflow_unsupported")


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


@pytest.fixture
def store_mock():
    store = MagicMock()
    store.load_user_token.return_value = {"refresh_token": "old-r"}
    with patch("lansenger_cli.commands.oauth.get_store", return_value=store):
        yield store


def run(args):
    return CliRunner().invoke(app, args)


# --- device-authorize ---


def test_device_authorize_success_rich():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = AUTH_OK
        result = run(["oauth", "device-authorize"])
    assert result.exit_code == 0
    assert "WDJB-MJHT" in result.stdout
    assert "device_verify" in result.stdout
    gc.return_value.request_device_authorization.assert_called_once_with(client_id="", source="CLI")


def test_device_authorize_json_shape():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = AUTH_OK
        result = run(["--json", "oauth", "device-authorize"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["device_code"] == "d" * 40
    assert data["interval"] == 5


def test_device_authorize_unsupported_exit_1_with_hint():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = UNSUPPORTED
        result = run(["oauth", "device-authorize"])
    assert result.exit_code == 1
    assert "authorize-url" in result.stdout


def test_device_authorize_unsupported_json_has_error_type():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = UNSUPPORTED
        result = run(["--json", "oauth", "device-authorize"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["error_type"] == "deviceflow_unsupported"


def test_device_authorize_from_option_passthrough():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = AUTH_OK
        run(["oauth", "device-authorize", "--from", "MCP", "--client-id", "cid-1"])
    gc.return_value.request_device_authorization.assert_called_once_with(client_id="cid-1", source="MCP")


# --- device-poll ---


def test_device_poll_pending_exit_0():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.poll_device_token.return_value = POLL_PENDING
        result = run(["oauth", "device-poll", "d" * 40])
    assert result.exit_code == 0
    assert "authorization_pending" in result.stdout


def test_device_poll_approved_exit_0_with_code():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.poll_device_token.return_value = POLL_APPROVED
        result = run(["oauth", "device-poll", "d" * 40])
    assert result.exit_code == 0
    assert "c" * 36 in result.stdout


def test_device_poll_denied_exit_1():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.poll_device_token.return_value = POLL_DENIED
        result = run(["oauth", "device-poll", "d" * 40])
    assert result.exit_code == 1


def test_device_poll_expired_exit_1():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.poll_device_token.return_value = POLL_EXPIRED
        result = run(["oauth", "device-poll", "d" * 40])
    assert result.exit_code == 1


def test_device_poll_wait_loops_with_server_interval():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.poll_device_token.side_effect = [POLL_PENDING, POLL_PENDING, POLL_APPROVED]
        with patch.object(oauth_mod, "_sleep") as sleep_mock:
            result = run(["oauth", "device-poll", "d" * 40, "--wait"])
    assert result.exit_code == 0
    assert gc.return_value.poll_device_token.call_count == 3
    sleep_mock.assert_called_with(5)


# --- device-login ---


def _login_client(store_mock, polls):
    client = MagicMock()
    client.request_device_authorization.return_value = AUTH_OK
    client.poll_device_token.side_effect = polls
    client.exchange_code.return_value = EXCHANGE_OK
    return client


def test_device_login_full_flow_saves_token(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep"), \
         patch.object(oauth_mod.webbrowser, "open") as wb:
        gc.return_value = _login_client(store_mock, [POLL_PENDING, POLL_APPROVED])
        result = run(["oauth", "device-login", "--no-browser"])
    assert result.exit_code == 0
    assert "user_token" in result.stdout
    wb.assert_not_called()
    store_mock.save_user_token.assert_called_once_with(
        "u" * 36, "r" * 36, 7200, 300, 2592000, staff_id="staff-001",
    )


def test_device_login_opens_browser_by_default(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep"), \
         patch.object(oauth_mod.webbrowser, "open") as wb:
        gc.return_value = _login_client(store_mock, [POLL_APPROVED])
        result = run(["oauth", "device-login"])
    assert result.exit_code == 0
    wb.assert_called_once_with(AUTH_OK.verification_uri_complete)


def test_device_login_denied_exit_1_no_exchange(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep"):
        client = _login_client(store_mock, [POLL_DENIED])
        gc.return_value = client
        result = run(["oauth", "device-login", "--no-browser"])
    assert result.exit_code == 1
    client.exchange_code.assert_not_called()
    store_mock.save_user_token.assert_not_called()


def test_device_login_timeout_exit_1(store_mock):
    times = iter([0, 10**9, 10**9 + 1])

    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_monotonic", side_effect=lambda: next(times, 10**9 + 2)), \
         patch.object(oauth_mod, "_sleep"):
        gc.return_value = _login_client(store_mock, [POLL_PENDING])
        result = run(["oauth", "device-login", "--no-browser", "--timeout", "5"])
    assert result.exit_code == 1
    assert "timeout" in (result.stdout + str(result.exception)).lower()


def test_device_login_keyboard_interrupt_exit_1(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep", side_effect=KeyboardInterrupt):
        gc.return_value = _login_client(store_mock, [POLL_PENDING, POLL_PENDING])
        result = run(["oauth", "device-login", "--no-browser"])
    assert result.exit_code == 1


def test_device_login_exchange_failure_exit_1_no_save(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep"):
        client = _login_client(store_mock, [POLL_APPROVED])
        client.exchange_code.return_value = fake_result(success=False, error="code expired")
        gc.return_value = client
        result = run(["oauth", "device-login", "--no-browser"])
    assert result.exit_code == 1
    store_mock.save_user_token.assert_not_called()


def test_device_login_unsupported_fallback_hint(store_mock):
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = UNSUPPORTED
        result = run(["oauth", "device-login"])
    assert result.exit_code == 1
    assert "local-callback" in result.stdout


def test_device_login_unsupported_json_stdout(store_mock):
    """降级输出统一沿用 output_result 契约：失败 = stdout 单文档（含 error_type）+ exit 1。"""
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = UNSUPPORTED
        result = run(["--json", "oauth", "device-login"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["error_type"] == "deviceflow_unsupported"


def test_device_poll_wait_timeout_exit_1():
    """--wait 到 deadline 仍 pending → exit 1（评审 P1：不得把超时当成功）。"""
    times = iter([0, 10**9, 10**9 + 1])
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_monotonic", side_effect=lambda: next(times, 10**9 + 2)), \
         patch.object(oauth_mod, "_sleep"):
        gc.return_value.poll_device_token.return_value = POLL_PENDING
        result = run(["oauth", "device-poll", "d" * 40, "--wait", "--timeout", "600"])
    assert result.exit_code == 1
    assert "pending" in result.stdout.lower()


def test_device_poll_keyboard_interrupt_exit_1():
    """--wait 轮询期 Ctrl-C → exit 1（遵守 C1 0/1/10；不得以信号码 130 退出）。"""
    with patch("lansenger_cli.commands.oauth.get_client") as gc, \
         patch.object(oauth_mod, "_sleep", side_effect=KeyboardInterrupt):
        gc.return_value.poll_device_token.return_value = POLL_PENDING
        result = run(["oauth", "device-poll", "d" * 40, "--wait"])
    assert result.exit_code == 1
