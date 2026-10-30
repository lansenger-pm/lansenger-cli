"""Tests for the `lansenger recording` command group."""

import json
import re
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_active_profile, set_json_output

runner = CliRunner()

# typer's option highlighter splits option names into styled runs when color
# output is enabled (e.g. on CI), so assertions must look at plain text.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def plain_text(text: str) -> str:
    return _ANSI_RE.sub("", text)


@pytest.fixture(autouse=True)
def _reset_global_state():
    set_json_output(False)
    set_active_profile("default")


class _Result:
    """Minimal stand-in for an SDK result object (no auto-created attrs)."""

    def __init__(self, success: bool = True, error: str = "", retryable: bool = False, **fields):
        self.success = success
        self.error = error
        self.retryable = retryable
        for key, value in fields.items():
            setattr(self, key, value)

    def to_dict(self):
        data = {"success": self.success}
        if self.error:
            data["error"] = self.error
        for key, value in vars(self).items():
            if key in ("success", "error", "retryable"):
                continue
            data[key] = value
        return data


RECORDINGS = [
    {
        "recordingId": "rec-1",
        "name": "周会录音",
        "duration": 63000,
        "state": 1,
        "convertState": 4,
        "summaryState": 5,
        "createTime": 1792721267905694,
    },
]
RECORDING_DETAIL = {
    "recordingId": "rec-1",
    "name": "周会录音",
    "hasAudio": True,
    "hasTranscription": True,
    "hasSummary": False,
}


def test_recording_group_registered():
    result = runner.invoke(app, ["recording", "--help"])
    assert result.exit_code == 0, result.output
    for command in ("list", "detail", "transcribe", "summary", "tags", "templates"):
        assert command in plain_text(result.output)


def test_list_passes_paging_and_renders_table():
    client = MagicMock()
    client.fetch_recording_list.return_value = _Result(recordings=RECORDINGS, total=1, has_more=False)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(
            app, ["recording", "list", "--page", "2", "--page-size", "5"], env={"COLUMNS": "200"},
        )
    assert result.exit_code == 0, result.output
    kwargs = client.fetch_recording_list.call_args.kwargs
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 5
    assert kwargs["user_token"] == ""
    output = plain_text(result.output)
    for column in ("recording_id", "duration(ms)", "convert_state", "summary_state", "create_time"):
        assert column in output
    assert "周会录音" in output
    assert "rec-1" in output
    assert "has_more" in output
    assert "total" in output


def test_list_json_outputs_full_data():
    client = MagicMock()
    client.fetch_recording_list.return_value = _Result(recordings=RECORDINGS, total=1, has_more=False)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "recording", "list"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["recordings"][0]["recordingId"] == "rec-1"
    assert payload["total"] == 1
    assert payload["has_more"] is False


def test_list_failure_exits_1():
    client = MagicMock()
    client.fetch_recording_list.return_value = _Result(success=False, error="boom")
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "list"])
    assert result.exit_code == 1
    assert "boom" in plain_text(result.output)


def test_detail_prints_all_fields_with_dashes():
    client = MagicMock()
    client.fetch_recording_detail.return_value = _Result(recording=RECORDING_DETAIL)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "detail", "rec-1"], env={"COLUMNS": "200"})
    assert result.exit_code == 0, result.output
    assert client.fetch_recording_detail.call_args.kwargs["recording_id"] == "rec-1"
    output = plain_text(result.output)
    for field in ("recordingId", "hasAudio", "hasTranscription", "hasSummary", "hasChapters", "chaptersId"):
        assert field in output
    assert "true" in output
    assert "false" in output
    assert "-" in output


def test_detail_json_outputs_full_data():
    client = MagicMock()
    client.fetch_recording_detail.return_value = _Result(recording=RECORDING_DETAIL)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "recording", "detail", "rec-1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["recording"]["recordingId"] == "rec-1"
    assert payload["recording"]["hasAudio"] is True


def test_detail_missing_recording_exits_0():
    client = MagicMock()
    client.fetch_recording_detail.return_value = _Result(recording=None)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "detail", "rec-1"])
    assert result.exit_code == 0, result.output


def test_transcribe_without_yes_exits_10():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["recording", "transcribe", "rec-1"])
    assert result.exit_code == 10
    assert "Confirmation required" in plain_text(result.output)
    runner_client.assert_not_called()


def test_transcribe_json_exit10_envelope():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["--json", "recording", "transcribe", "rec-1"])
    assert result.exit_code == 10
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "confirmation_required"
    assert payload["error"]["risk"]["level"] == "high-risk-write"
    assert payload["error"]["risk"]["action"] == "transcribe recording rec-1"
    runner_client.assert_not_called()


def test_transcribe_dry_run_exits_0_no_call():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["recording", "transcribe", "rec-1", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in plain_text(result.output)
    runner_client.assert_not_called()


def test_transcribe_dry_run_json():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["--json", "recording", "transcribe", "rec-1", "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["would_perform"] == "transcribe recording rec-1"
    runner_client.assert_not_called()


def test_transcribe_with_yes_calls_client():
    client = MagicMock()
    client.create_transcription_task.return_value = _Result(recording_id="rec-1", convert_state=5)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "transcribe", "rec-1", "--yes"])
    assert result.exit_code == 0, result.output
    kwargs = client.create_transcription_task.call_args.kwargs
    assert kwargs["recording_id"] == "rec-1"
    assert kwargs["user_token"] == ""
    output = plain_text(result.output)
    assert "rec-1" in output
    assert "5" in output


def test_transcribe_json_with_yes_outputs_result():
    client = MagicMock()
    client.create_transcription_task.return_value = _Result(recording_id="rec-1", convert_state=5)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "recording", "transcribe", "rec-1", "--yes"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["recording_id"] == "rec-1"
    assert payload["convert_state"] == 5


def test_summary_without_yes_exits_10():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["recording", "summary", "rec-1"])
    assert result.exit_code == 10
    assert "Confirmation required" in plain_text(result.output)
    runner_client.assert_not_called()


def test_summary_json_exit10_envelope():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(app, ["--json", "recording", "summary", "rec-1"])
    assert result.exit_code == 10
    payload = json.loads(result.stderr)
    assert payload["error"]["risk"]["action"] == "summarize recording rec-1"
    runner_client.assert_not_called()


def test_summary_dry_run_no_call():
    runner_client = MagicMock()
    with patch("lansenger_cli.commands.recording.get_client", runner_client):
        result = runner.invoke(
            app, ["recording", "summary", "rec-1", "--template-id", "tpl-1", "--dry-run"],
        )
    assert result.exit_code == 0
    assert "DRY RUN" in plain_text(result.output)
    runner_client.assert_not_called()


def test_summary_with_yes_calls_client_and_prints_state():
    client = MagicMock()
    client.create_summary_task.return_value = _Result(recording_id="rec-1", summary_state=5)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(
            app, ["recording", "summary", "rec-1", "--template-id", "tpl-1", "--yes"],
        )
    assert result.exit_code == 0, result.output
    kwargs = client.create_summary_task.call_args.kwargs
    assert kwargs["recording_id"] == "rec-1"
    assert kwargs["template_id"] == "tpl-1"
    output = plain_text(result.output)
    assert "summary_state" in output
    assert "5" in output


def test_summary_without_template_passes_none():
    client = MagicMock()
    client.create_summary_task.return_value = _Result(recording_id="rec-1", summary_state=5)
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "summary", "rec-1", "--yes"])
    assert result.exit_code == 0, result.output
    assert client.create_summary_task.call_args.kwargs["template_id"] is None


def test_tags_renders_table():
    client = MagicMock()
    client.fetch_recording_tags.return_value = _Result(
        tags=[{"tagId": "tag-1", "name": "重点", "sortWeight": 1.5, "createTime": 1792721267905694}],
    )
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "tags"], env={"COLUMNS": "200"})
    assert result.exit_code == 0, result.output
    output = plain_text(result.output)
    for column in ("tag_id", "name", "sort_weight", "create_time"):
        assert column in output
    assert "重点" in output
    assert "tag-1" in output


def test_tags_json_outputs_full_data():
    client = MagicMock()
    client.fetch_recording_tags.return_value = _Result(
        tags=[{"tagId": "tag-1", "name": "重点", "sortWeight": 1.5, "createTime": 1792721267905694}],
    )
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "recording", "tags"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["tags"][0]["tagId"] == "tag-1"


def test_templates_passes_paging_and_renders_table():
    client = MagicMock()
    client.fetch_recording_templates.return_value = _Result(
        templates=[{"templateId": "tpl-1", "name": "周报模板", "templateState": 1, "orderNumber": 7}],
        total=1,
        has_more=False,
    )
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(
            app, ["recording", "templates", "--page", "2", "--page-size", "5"], env={"COLUMNS": "200"},
        )
    assert result.exit_code == 0, result.output
    kwargs = client.fetch_recording_templates.call_args.kwargs
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 5
    output = plain_text(result.output)
    for column in ("template_id", "name", "template_state", "order"):
        assert column in output
    assert "tpl-1" in output
    assert "周报模板" in output
    assert "7" in output
    assert "has_more" in output
    assert "total" in output


def test_templates_json_outputs_full_data():
    client = MagicMock()
    client.fetch_recording_templates.return_value = _Result(
        templates=[{"templateId": "tpl-1", "name": "周报模板", "templateState": 1, "orderNumber": 7}],
        total=1,
        has_more=False,
    )
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["--json", "recording", "templates"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["templates"][0]["templateId"] == "tpl-1"
    assert payload["has_more"] is False


def test_tags_failure_exits_1():
    client = MagicMock()
    client.fetch_recording_tags.return_value = _Result(success=False, error="denied")
    with patch("lansenger_cli.commands.recording.get_client", return_value=client):
        result = runner.invoke(app, ["recording", "tags"])
    assert result.exit_code == 1
    assert "denied" in plain_text(result.output)
