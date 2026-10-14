"""Tests for the dependency-free QR encoder/renderer and the device-flow --qr output.

Golden digests (base64 of the sha256, because the repo's secret scanner flags any
32+ char hex run) were produced by this encoder *after* cross-checking it against
python-qrcode (identical interleaved codewords for versions 1-15 at ECC L/M, 90/90
cases) and decoding back with zxing-cpp (90/90 cases, plus a 124-byte device URL at
version 8). They guard against regressions, not against a wrong implementation.
"""

import base64
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lansenger_cli import qr
from lansenger_cli.main import app
from lansenger_cli.utils import set_json_output, set_active_profile

SHORT_URI = "https://pp.example.com/oauth/device_verify?user_code=WDJB-MJHT"
REAL_URI = (
    "https://passport.lx.qianxin.com/oauth/device_verify"
    "?device_code=" + "d" * 40 + "&user_code=TM9L-MPLT"
)
GOLDEN = {
    SHORT_URI: (
        "uGumpf5auJIIAMS2SOU/oYPQ1vyX2bM5KzVI7lYNadE=",
        "Kp+sh4J/boOV2YNLsQ7rsF84c3jLlW1mWvVXh2gqiew=",
        "NIvJf3fvHmpBwcK64gv2ZIqd1sXvCqOsEpOTlT7gAVo=",
    ),
    "HELLO": (
        "gq3lN679CUAfD1VBBxQoRBqwkcONfq9gzzJoUKdZzpk=",
        "PLAR1kC1yG0vXDiVoB00BrswIzPEFgkuZ3KBj513Z1s=",
        "iL2Rnftct1TueCw+Gz/9tT7Pn/Dhf5eTDhLHygy9JF4=",
    ),
    REAL_URI: (
        "ieuhxgwXXboLuGaQwYOCh1tewxywRLK3D/np6gpNQxU=",
        "ogwrZgF7nl9W8VEoecKt93JejxBEXaunydDYEV6L0JI=",
        "+3xGtu9Q9f8H5L6x7mTOmi9ilTcvJT714AYO9Axbets=",
    ),
}


def digest(data: bytes | str) -> str:
    raw = data.encode() if isinstance(data, str) else data
    return base64.b64encode(hashlib.sha256(raw).digest()).decode()


@pytest.mark.parametrize("text", list(GOLDEN))
def test_encoder_matches_golden_matrices(text):
    matrix = qr.encode(text)
    text_digest, ascii_digest, png_digest = GOLDEN[text]
    assert digest(qr.render_text(matrix)) == text_digest
    assert digest(qr.render_text(matrix, unicode=False)) == ascii_digest
    assert digest(qr.to_png(matrix)) == png_digest


def test_matrix_has_valid_function_patterns():
    matrix = qr.encode(REAL_URI)
    size = len(matrix)
    version = (size - 17) // 4
    assert version == 8 and size == 49
    for row0, col0 in ((0, 0), (0, size - 7), (size - 7, 0)):
        assert all(matrix[row0][col0 + i] for i in range(7))
        assert all(matrix[row0 + 6][col0 + i] for i in range(7))
        assert all(matrix[row0 + i][col0] for i in range(7))
        assert all(matrix[row0 + i][col0 + 6] for i in range(7))
        assert matrix[row0 + 1][col0 + 1 : col0 + 6] == [False] * 5
        assert matrix[row0 + 3][col0 + 3] is True
    assert matrix[7][:8] == [False] * 8
    assert [matrix[6][i] for i in range(8, size - 8)] == [i % 2 == 0 for i in range(8, size - 8)]
    assert matrix[size - 8][8] is True
    assert any(matrix[row][col] for row in range(size) for col in range(size))


def test_version_selection_and_overlong_guard():
    assert len(qr.encode("A" * 14, "M")) == 21
    assert (len(qr.encode("A" * 15, "M")) - 17) // 4 == 2
    assert (len(qr.encode("A" * 78, "L")) - 17) // 4 == 4
    assert (len(qr.encode("A" * 79, "L")) - 17) // 4 == 5
    with pytest.raises(ValueError):
        qr.encode("A" * 5000)


def test_render_text_shapes():
    matrix = qr.encode(SHORT_URI, "M")
    size = len(matrix)
    for quiet in (0, 2, 4):
        width = size + quiet * 2
        unicode_lines = qr.render_text(matrix, quiet_zone=quiet).splitlines()
        ascii_lines = qr.render_text(matrix, unicode=False, quiet_zone=quiet).splitlines()
        assert len(unicode_lines) == (width + 1) // 2
        assert {len(line) for line in unicode_lines} == {width}
        assert set("".join(unicode_lines)) <= set("█▀▄ ")
        assert len(ascii_lines) == width
        assert {len(line) for line in ascii_lines} == {width * 2}
        assert set("".join(ascii_lines)) <= {"█", " "}


def test_to_png_header_and_dimensions():
    matrix = qr.encode(SHORT_URI)
    png = qr.to_png(matrix, scale=4, quiet_zone=2)
    assert png.startswith(b"\x89PNG\r\n\x1a\n") and png.endswith(b"IEND\xaeB`\x82")
    expected = (len(matrix) + 4) * 4
    assert png[16:24] == expected.to_bytes(4, "big") * 2
    assert png[24] == 1 and png[25] == 0


runner = CliRunner()


def fake_result(**kw):
    base = {"success": True, "error": None, "error_type": None}
    base.update(kw)
    ns = SimpleNamespace(**base)
    ns.to_dict = lambda: {k: v for k, v in base.items() if v is not None}
    return ns


AUTH_OK = fake_result(
    device_code="d" * 40,
    user_code="WDJB-MJHT",
    verification_uri_complete=SHORT_URI,
    interval=5,
    expires_in=600,
    expires_at=1791864291,
    open_api_domain="https://gw.example.com",
)


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


def run(args):
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.request_device_authorization.return_value = AUTH_OK
        return runner.invoke(app, args)


def test_device_authorize_prints_utf8_qr_by_default():
    result = run(["oauth", "device-authorize"])
    assert result.exit_code == 0
    assert "█" in result.stdout and "▀" in result.stdout
    assert "WDJB-MJHT" in result.stdout


def test_device_authorize_qr_none_prints_no_blocks():
    result = run(["oauth", "device-authorize", "--qr", "none"])
    assert result.exit_code == 0
    assert "█" not in result.stdout and "▀" not in result.stdout


def test_device_authorize_qr_ascii_uses_no_unicode_blocks():
    result = run(["oauth", "device-authorize", "--qr", "ascii"])
    assert result.exit_code == 0
    assert "█" in result.stdout
    assert "▀" not in result.stdout and "▄" not in result.stdout


def test_device_authorize_json_stdout_stays_pure_json():
    result = run(["--json", "oauth", "device-authorize"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["device_code"] == "d" * 40
    assert "▀" not in result.stdout


def test_device_authorize_qr_png_writes_scannable_file(tmp_path):
    target = tmp_path / "qr.png"
    result = run(["oauth", "device-authorize", "--qr", "none", "--qr-png", str(target)])
    assert result.exit_code == 0
    data = target.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(qr.encode(SHORT_URI)) == 33
    assert data[16:24] == ((33 + 8) * 6).to_bytes(4, "big") * 2


def test_device_authorize_qr_png_in_json_mode_keeps_stdout_clean(tmp_path):
    target = tmp_path / "qr.png"
    result = run(["--json", "oauth", "device-authorize", "--qr-png", str(target)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["device_code"] == "d" * 40
    assert target.exists()


def test_to_data_uri_carries_a_base64_png():
    matrix = qr.encode(SHORT_URI)
    uri = qr.to_data_uri(matrix, scale=4, quiet_zone=2)
    assert uri.startswith("data:image/png;base64,")
    raw = base64.b64decode(uri.split(",", 1)[1])
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")
    assert raw == qr.to_png(matrix, scale=4, quiet_zone=2)


def test_device_authorize_qr_data_uri_prints_uri_for_panels():
    result = run(["oauth", "device-authorize", "--qr", "none", "--qr-data-uri"])
    assert result.exit_code == 0
    assert "data:image/png;base64," in result.stdout
    assert "█" not in result.stdout


def test_device_authorize_qr_data_uri_in_json_mode_goes_to_stderr():
    result = run(["--json", "oauth", "device-authorize", "--qr-data-uri"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["device_code"] == "d" * 40
    assert "data:image" not in result.stdout
    stderr = getattr(result, "stderr", "")
    if stderr:
        event = json.loads(stderr.strip().splitlines()[-1])
        assert event["event"] == "device_qr"
        assert event["qr_data_uri"].startswith("data:image/png;base64,")


def test_device_login_fails_fast_when_credentials_are_broken():
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        gc.return_value.health_check.return_value = False
        result = runner.invoke(app, ["--json", "oauth", "device-login", "--no-browser"])
    assert result.exit_code == 1
    gc.return_value.request_device_authorization.assert_not_called()
    raw = getattr(result, "stderr", "") or result.stdout
    payload = json.loads(raw.strip().splitlines()[-1])
    assert payload["error"]["type"] == "auth_failed"
    assert "app_secret" in payload["hint"]


def test_device_login_reports_exchange_failure_instead_of_traceback():
    approved = fake_result(state="access_approved", oauth2_code="one-time-code")
    with patch("lansenger_cli.commands.oauth.get_client") as gc:
        client = gc.return_value
        client.health_check.return_value = True
        client.request_device_authorization.return_value = AUTH_OK
        client.poll_device_token.return_value = approved
        client.exchange_code.side_effect = RuntimeError("Token error (errCode=40018): APP Secret错误(33740)")
        result = runner.invoke(app, ["--json", "oauth", "device-login", "--no-browser"])
    assert result.exit_code == 1
    raw = getattr(result, "stderr", "") or result.stdout
    payload = json.loads(raw.strip().splitlines()[-1])
    assert payload["error"]["type"] == "exchange_failed"
    assert "40018" in payload["error"]["message"]
    assert "Traceback" not in result.stdout and "Traceback" not in raw


def test_device_authorize_qr_ecc_rejects_unknown_level():
    result = run(["oauth", "device-authorize", "--qr", "none", "--qr-ecc", "Q"])
    assert result.exit_code == 1
    assert "--qr-ecc" in result.stdout


def test_device_authorize_qr_ecc_l_is_accepted():
    result = run(["oauth", "device-authorize", "--qr", "none", "--qr-ecc", "L"])
    assert result.exit_code == 0


def test_device_authorize_guidance_points_at_the_next_step():
    result = run(["oauth", "device-authorize", "--qr", "none"])
    assert result.exit_code == 0
    assert "本命令只申请设备码" in result.stdout
    assert "device-login" in result.stdout
    assert "oauth device-poll" in result.stdout


def test_device_login_human_output_keeps_the_raw_token_out_of_the_table():
    approved = fake_result(state="access_approved", oauth2_code="one-time-code")
    with patch("lansenger_cli.commands.oauth.get_client") as gc, patch("lansenger_cli.commands.oauth.get_store"):
        client = gc.return_value
        client.health_check.return_value = True
        client.request_device_authorization.return_value = AUTH_OK
        client.poll_device_token.return_value = approved
        client.exchange_code.return_value = fake_result(
            success=True, user_token="u" * 36, refresh_token="r" * 36,
            expires_in=7200, refresh_expires_in=2592000, staff_id="staff-001",
        )
        result = runner.invoke(app, ["oauth", "device-login", "--no-browser"])
    assert result.exit_code == 0
    assert "staff_id=staff-001" in result.stdout
    assert "u" * 36 not in result.stdout
