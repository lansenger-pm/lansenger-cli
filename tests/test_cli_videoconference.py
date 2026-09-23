"""Tests for the `lansenger videoconference` command group."""

import re
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_sdk.models import (
    VideoconferenceConfResult,
    VideoconferenceDetailResult,
    VideoconferenceListResult,
    VideoconferenceOpResult,
    VideoconferenceParamResult,
    VideoconferenceStatusListResult,
    VideoconferenceVodListResult,
    VideoconferenceVodUrlResult,
)

runner = CliRunner()

# typer's option highlighter splits option names into styled runs when color
# output is enabled (e.g. on CI), so assertions must look at plain text.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def plain_text(text: str) -> str:
    return _ANSI_RE.sub("", text)

HOST_MEMBER = '[{"staffId":"u1","employeeName":"Host","role":"admin"},{"staffId":"u2","employeeName":"B","role":"participant"}]'


def test_videoconference_group_registered():
    result = runner.invoke(app, ["videoconference", "--help"])
    assert result.exit_code == 0, result.output
    for command in (
        "create", "modify", "cancel", "stop", "detail", "list",
        "record-list", "simplerecord", "fixroom-list", "status",
        "subscribe", "params", "history", "active", "member-control",
        "invite", "member-list", "vod-list", "vod-download", "org-conf",
    ):
        assert command in result.output


def test_create_meeting_parses_members():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.create_meeting.return_value = VideoconferenceDetailResult(
            success=True, mid=123, subject="周会",
        )
        gc.return_value = client
        result = runner.invoke(app, [
            "videoconference", "create", "周会", "org1",
            "--start-time", "1700000000000", "--member", HOST_MEMBER,
            "--type", "1", "--auto-record", "1",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.create_meeting.call_args.kwargs
    assert kwargs["subject"] == "周会"
    assert kwargs["org_id"] == "org1"
    assert kwargs["start_time"] == 1700000000000
    assert kwargs["type"] == 1
    assert kwargs["auto_record"] == 1
    assert kwargs["members"][0]["role"] == "admin"
    assert "123" in result.output


def test_create_meeting_requires_exactly_one_host():
    result = runner.invoke(app, [
        "videoconference", "create", "周会", "org1",
        "--start-time", "1700000000000",
        "--member", '[{"staffId":"u1","employeeName":"A","role":"participant"}]',
    ])
    assert result.exit_code != 0
    assert "role='admin'" in result.output

    two_hosts = runner.invoke(app, [
        "videoconference", "create", "周会", "org1",
        "--start-time", "1700000000000",
        "--member", '[{"staffId":"u1","role":"admin"},{"staffId":"u2","role":"admin"}]',
    ])
    assert two_hosts.exit_code != 0


def test_modify_meeting_passes_fields():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.modify_meeting.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client
        result = runner.invoke(app, [
            "videoconference", "modify", "123", "org1", "staff9",
            "--subject", "新主题", "--start-time", "1800000000000",
            "--member", HOST_MEMBER,
            "--user-stop-time", "1800003600000",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.modify_meeting.call_args.kwargs
    assert kwargs["mid"] == 123
    assert kwargs["operator"] == "staff9"
    assert kwargs["subject"] == "新主题"
    assert kwargs["start_time"] == 1800000000000
    # 与 create 对齐：modify 也必须能透传自动结束时间
    assert kwargs["user_stop_time"] == 1800003600000


def test_modify_meeting_omits_user_stop_time_when_not_given():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.modify_meeting.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client
        result = runner.invoke(app, [
            "videoconference", "modify", "123", "org1", "staff9",
            "--subject", "新主题", "--start-time", "1800000000000",
            "--member", HOST_MEMBER,
        ])
    assert result.exit_code == 0, result.output
    assert client.modify_meeting.call_args.kwargs["user_stop_time"] is None


def test_cancel_and_stop_require_confirmation():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.cancel_meeting.return_value = VideoconferenceOpResult(success=True, done=True)
        client.stop_meeting.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client
        cancel_gate = runner.invoke(app, ["videoconference", "cancel", "123", "org1", "staff9"])
        stop_gate = runner.invoke(app, ["videoconference", "stop", "123", "org1", "staff9"])
        assert cancel_gate.exit_code == 10, cancel_gate.output
        assert stop_gate.exit_code == 10, stop_gate.output
        client.cancel_meeting.assert_not_called()
        client.stop_meeting.assert_not_called()

        cancel_ok = runner.invoke(app, ["videoconference", "cancel", "123", "org1", "staff9", "--yes"])
        stop_dry = runner.invoke(app, ["videoconference", "stop", "123", "org1", "staff9", "--dry-run"])
    assert cancel_ok.exit_code == 0, cancel_ok.output
    assert stop_dry.exit_code == 0, stop_dry.output
    client.cancel_meeting.assert_called_once_with(
        mid=123, org_id="org1", operator="staff9", user_token="",
    )
    client.stop_meeting.assert_not_called()  # dry run never hits the client


def test_meeting_detail_passes_identity():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.fetch_meeting_detail.return_value = VideoconferenceDetailResult(
            success=True, mid=123, subject="周会", status=4,
        )
        gc.return_value = client
        result = runner.invoke(app, ["videoconference", "detail", "123", "org1", "staff9"])
    assert result.exit_code == 0, result.output
    client.fetch_meeting_detail.assert_called_once_with(
        mid=123, org_id="org1", operator="staff9", user_token="",
    )


def test_meeting_list_validates_person_range():
    result = runner.invoke(app, [
        "videoconference", "list", "org1",
        "--start-time", "1", "--end-time", "2", "--fetch-range", "person",
    ])
    assert result.exit_code != 0
    assert "--staff-id" in plain_text(result.output)


def test_meeting_list_passes_params():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.fetch_meeting_list.return_value = VideoconferenceListResult(
            success=True, offset=0, total=1,
            items=[{"id": 123, "subject": "周会", "status": 0}],
        )
        gc.return_value = client
        result = runner.invoke(app, [
            "videoconference", "list", "org1",
            "--start-time", "1", "--end-time", "2",
            "--fetch-range", "person", "--staff-id", "u1", "--limit", "5",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.fetch_meeting_list.call_args.kwargs
    assert kwargs["fetch_range"] == "person"
    assert kwargs["staff_id"] == "u1"
    assert kwargs["limit"] == 5
    assert "周会" in result.output


def test_status_requires_mids():
    result = runner.invoke(app, ["videoconference", "status", "org1", "--mids", ", ,"])
    assert result.exit_code != 0

    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.fetch_meeting_status.return_value = VideoconferenceStatusListResult(
            success=True, statuses=[{"mid": 123, "status": 1}],
        )
        gc.return_value = client
        ok = runner.invoke(app, ["videoconference", "status", "org1", "--mids", "123,456"])
    assert ok.exit_code == 0, ok.output
    kwargs = client.fetch_meeting_status.call_args.kwargs
    assert kwargs["mids"] == ["123", "456"]


def test_member_control_passes_op_code_through():
    """op_code 不做客户端校验：未知值也原样透传给 SDK（服务端才是权威）。"""
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.control_member.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client
        unknown = runner.invoke(app, [
            "videoconference", "member-control", "123", "u1", "zzz_not_an_op", "org1", "staff9",
        ])
    assert unknown.exit_code == 0, unknown.output
    assert client.control_member.call_args.kwargs["op_code"] == "zzz_not_an_op"

    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.control_member.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client
        ok = runner.invoke(app, [
            "videoconference", "member-control", "123", "u1", "muteall", "org1", "staff9",
        ])
    assert ok.exit_code == 0, ok.output
    kwargs = client.control_member.call_args.kwargs
    assert kwargs["op_code"] == "muteall"


def test_vod_download_validates_vod_limit():
    too_many = runner.invoke(app, [
        "videoconference", "vod-download", "org1", "staff9",
        "--vods", '[{"vodId":"a"},{"vodId":"b"},{"vodId":"c"},{"vodId":"d"}]',
    ])
    assert too_many.exit_code != 0

    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.fetch_vod_download_urls.return_value = VideoconferenceVodUrlResult(
            success=True, data={"urls": ["https://x"]},
        )
        gc.return_value = client
        ok = runner.invoke(app, [
            "videoconference", "vod-download", "org1", "staff9",
            "--vods", '[{"vodId":"a"},{"vodId":"b"}]',
        ])
    assert ok.exit_code == 0, ok.output
    kwargs = client.fetch_vod_download_urls.call_args.kwargs
    assert kwargs["vods"] == [{"vodId": "a"}, {"vodId": "b"}]


def test_read_only_commands_pass_parameters():
    with patch("lansenger_cli.commands.videoconference.get_client") as gc:
        client = MagicMock()
        client.fetch_meeting_record_list.return_value = VideoconferenceListResult(success=True)
        client.fetch_member_simplerecord.return_value = VideoconferenceListResult(success=True)
        client.fetch_fixroom_list.return_value = VideoconferenceListResult(success=True)
        client.subscribe_meeting_events.return_value = VideoconferenceOpResult(success=True, done=True)
        client.fetch_meeting_params.return_value = VideoconferenceParamResult(success=True)
        client.fetch_history_meetings.return_value = VideoconferenceListResult(success=True)
        client.fetch_active_meetings.return_value = VideoconferenceListResult(success=True)
        client.fetch_member_list.return_value = VideoconferenceListResult(success=True)
        client.fetch_vod_list.return_value = VideoconferenceVodListResult(success=True)
        client.fetch_org_videoconference_conf.return_value = VideoconferenceConfResult(success=True)
        client.invite_members.return_value = VideoconferenceOpResult(success=True, done=True)
        gc.return_value = client

        invokes = [
            (["videoconference", "record-list", "org1",
              "--start-time", "1", "--end-time", "2", "--create-source", "1"],
             client.fetch_meeting_record_list,
             {"org_id": "org1", "start_time": 1, "end_time": 2, "admin": "",
              "create_source": 1, "limit": 10, "offset": 0, "user_token": ""}),
            (["videoconference", "simplerecord", "123", "org1", "staff9",
              "--limit", "5", "--offset", "2"],
             client.fetch_member_simplerecord,
             {"mid": 123, "org_id": "org1", "operator": "staff9",
              "limit": 5, "offset": 2, "user_token": ""}),
            (["videoconference", "fixroom-list", "org1", "staff9"],
             client.fetch_fixroom_list,
             {"org_id": "org1", "operator": "staff9",
              "limit": 10, "offset": 0, "user_token": ""}),
            (["videoconference", "subscribe", "123", "org1",
              "--events", '[{"eventType":1}]', "--call-back-info", "cb"],
             client.subscribe_meeting_events,
             {"mid": 123, "org_id": "org1", "events": [{"eventType": 1}],
              "call_back_info": "cb", "user_token": ""}),
            (["videoconference", "params", "MN1", "org1", "staff9"],
             client.fetch_meeting_params,
             {"meeting_number": "MN1", "org_id": "org1", "operator": "staff9",
              "user_token": ""}),
            (["videoconference", "history", "org1", "staff9"],
             client.fetch_history_meetings,
             {"org_id": "org1", "operator": "staff9",
              "limit": 10, "offset": 0, "user_token": ""}),
            (["videoconference", "active", "org1", "staff9"],
             client.fetch_active_meetings,
             {"org_id": "org1", "operator": "staff9",
              "limit": 10, "offset": 0, "user_token": ""}),
            (["videoconference", "member-list", "123", "org1", "staff9"],
             client.fetch_member_list,
             {"mid": 123, "org_id": "org1", "operator": "staff9",
              "limit": 10, "offset": 0, "user_token": ""}),
            (["videoconference", "vod-list", "123", "org1", "staff9"],
             client.fetch_vod_list,
             {"mid": 123, "org_id": "org1", "operator": "staff9", "user_token": ""}),
            (["videoconference", "org-conf", "org1",
              "--meeting-number", "MN1", "--operator", "staff9"],
             client.fetch_org_videoconference_conf,
             {"org_id": "org1", "meeting_number": "MN1", "operator": "staff9",
              "user_token": ""}),
            (["videoconference", "invite", "MN1", "org1", "staff9",
              "--member", '[{"staffId":"u1","employeeName":"A","type":0,"video":1,"audio":1}]'],
             client.invite_members,
             {"meeting_number": "MN1", "org_id": "org1", "operator": "staff9",
              "members": [{"staffId": "u1", "employeeName": "A", "type": 0,
                           "video": 1, "audio": 1}], "user_token": ""}),
        ]

        for argv, method, expected in invokes:
            r = runner.invoke(app, argv)
            assert r.exit_code == 0, f"{argv}: {r.output}"
            method.assert_called_once_with(**expected)


def test_member_json_must_be_a_list():
    result = runner.invoke(app, [
        "videoconference", "invite", "MN1", "org1", "staff9",
        "--member", '{"staffId":"u1"}',
    ])
    assert result.exit_code != 0
    assert "JSON list" in result.output
