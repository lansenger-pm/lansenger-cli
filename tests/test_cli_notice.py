"""Tests for the `lansenger notice` command group."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import _AutoUserTokenProxy
from lansenger_sdk.models import NoticeAccountListResult, NoticeSendResult

runner = CliRunner()


def test_notice_group_registered():
    result = runner.invoke(app, ["notice", "--help"])
    assert result.exit_code == 0
    assert "send" in result.output
    assert "accounts" in result.output


def test_accounts_outputs_rows():
    with patch("lansenger_cli.commands.notice.get_client") as gc:
        client = MagicMock()
        client.fetch_notice_accounts.return_value = NoticeAccountListResult(
            success=True,
            total=2,
            accounts=[
                {"roleName": "行政通知", "officialNumberId": "1001", "code": "ACC001"},
                {"roleName": "安全通知", "officialNumberId": "1002", "code": "ACC002"},
            ],
        )
        gc.return_value = client
        result = runner.invoke(app, ["notice", "accounts", "--org-id", "org1"])
    assert result.exit_code == 0, result.output
    client.fetch_notice_accounts.assert_called_once_with(org_id="org1", user_token="")
    assert "ACC001" in result.output
    assert "行政通知" in result.output


def test_send_passes_parsed_lists():
    with patch("lansenger_cli.commands.notice.get_client") as gc:
        client = MagicMock()
        client.send_notice.return_value = NoticeSendResult(success=True, notice_code="NTC1", notice_status=2)
        gc.return_value = client
        result = runner.invoke(app, [
            "notice", "send", "系统升级通知", "ACC001",
            "--content", "正文内容",
            "--release-phones", "13800138000,13800138001",
            "--cc-phones", "13800138002",
            "--create-mobile", "13800138000",
            "--confirm-flag", "1",
            "--remind-status", "1",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.send_notice.call_args.kwargs
    assert kwargs["title"] == "系统升级通知"
    assert kwargs["account_code"] == "ACC001"
    assert kwargs["release_phones"] == ["13800138000", "13800138001"]
    assert kwargs["cc_phones"] == ["13800138002"]
    assert kwargs["confirm_flag"] == 1
    assert kwargs["remind_status"] == 1


def test_send_release_range_json():
    with patch("lansenger_cli.commands.notice.get_client") as gc:
        client = MagicMock()
        client.send_notice.return_value = NoticeSendResult(success=True, notice_code="NTC2")
        gc.return_value = client
        result = runner.invoke(app, [
            "notice", "send", "部门通知", "ACC001",
            "--content", "周报",
            "--user-type", "2",
            "--release-range", '[{"objId":"dept-1","objName":"研发部","objType":2}]',
            "--cc-staff-ids", "staff-002",
            "--create-user-id", "staff-001",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.send_notice.call_args.kwargs
    assert kwargs["user_type"] == 2
    assert kwargs["release_range"] == [{"objId": "dept-1", "objName": "研发部", "objType": 2}]
    assert kwargs["cc_staff_ids"] == ["staff-002"]


def test_send_api_error_exits_1():
    with patch("lansenger_cli.commands.notice.get_client") as gc:
        client = MagicMock()
        client.send_notice.return_value = NoticeSendResult(success=False, error="API error (errCode=3123): 人员不存在")
        gc.return_value = client
        result = runner.invoke(app, [
            "notice", "send", "t", "ACC001",
            "--content", "c",
            "--release-phones", "13800138000",
            "--create-mobile", "13800138000",
        ])
    assert result.exit_code == 1
    assert "errCode=3123" in result.output


def test_auto_proxy_injects_create_user_id_for_notice():
    raw_client = MagicMock()
    raw_client.send_notice.return_value = NoticeSendResult(success=True)
    store = MagicMock()

    with patch(
        "lansenger_cli.utils._load_and_refresh_user_token",
        return_value="user-token",
    ):
        client = _AutoUserTokenProxy(raw_client, store, "staff-001")
        result = client.send_notice(
            create_user_id="",
            user_token="",
        )

    assert result.success is True
    raw_client.send_notice.assert_called_once_with(
        create_user_id="staff-001",
        user_token="user-token",
    )
