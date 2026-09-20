"""Tests for the `lansenger boardroom` command group."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_sdk.models import (
    BoardroomGradingListResult,
    BoardroomListResult,
    BoardroomOpResult,
    BoardroomReserveResult,
)

runner = CliRunner()


def test_boardroom_group_registered():
    result = runner.invoke(app, ["boardroom", "--help"])
    assert result.exit_code == 0
    for name in ("rooms", "reserve", "cancel", "gradings", "schedule"):
        assert name in result.output


def test_gradings_outputs_rows():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        client = MagicMock()
        client.fetch_boardroom_gradings.return_value = BoardroomGradingListResult(
            success=True, total=1,
            gradings=[{"id": "g1", "name": "默认分级", "type": "GRADING_ADMIN"}],
        )
        gc.return_value = client
        result = runner.invoke(app, ["boardroom", "gradings"])
    assert result.exit_code == 0, result.output
    assert "g1" in result.output and "默认分级" in result.output


def test_rooms_renders_page():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        client = MagicMock()
        client.fetch_boardroom_list.return_value = BoardroomListResult(
            success=True, count=1,
            items=[{"id": "room1", "name": "第一会议室", "areaName": "望京",
                    "areaOfficeFoolerName": "3层", "peopleNum": 20}],
        )
        gc.return_value = client
        result = runner.invoke(app, ["boardroom", "rooms", "--grading-id", "g1"])
    assert result.exit_code == 0, result.output
    assert "第一会议室" in result.output
    kwargs = client.fetch_boardroom_list.call_args.kwargs
    assert kwargs["grading_id"] == "g1"


def test_reserve_passes_repeat_days():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        client = MagicMock()
        client.reserve_boardroom.return_value = BoardroomReserveResult(
            success=True, reserve_id="res1", reserve_code="BR1")
        gc.return_value = client
        result = runner.invoke(app, [
            "boardroom", "reserve", "room1", "周会",
            "--grading-id", "g1", "--start", "2026-07-22 09:00:00",
            "--end", "2026-07-22 10:00:00", "--notice-time", "会前15分钟",
            "--repeat-type", "week", "--repeat-days", "1,3,5",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.reserve_boardroom.call_args.kwargs
    assert kwargs["repeat_type"] == "week"
    assert kwargs["repeat_days"] == [1, 3, 5]


def test_cancel_requires_yes():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        result = runner.invoke(app, ["boardroom", "cancel", "res1"])
    assert result.exit_code == 10
    gc.assert_not_called()


def test_cancel_dry_run():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        result = runner.invoke(app, ["boardroom", "cancel", "res1", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    gc.assert_not_called()


def test_cancel_with_yes_executes():
    with patch("lansenger_cli.commands.boardroom.get_client") as gc:
        client = MagicMock()
        client.cancel_boardroom_reserve.return_value = BoardroomOpResult(success=True, done=True)
        gc.return_value = client
        result = runner.invoke(app, ["boardroom", "cancel", "res1", "--yes", "--reason", "改期"])
    assert result.exit_code == 0, result.output
    kwargs = client.cancel_boardroom_reserve.call_args.kwargs
    assert kwargs["cancel_reason"] == "改期"


def test_schedule_requires_grading_id():
    result = runner.invoke(app, ["boardroom", "schedule", "room1", "2026-07-22"])
    assert result.exit_code != 0
