import json
from typing import Optional

import typer
from rich.table import Table

from lansenger_cli.utils import (
    confirm_high_risk,
    console,
    get_client,
    is_json_output,
    output_list,
    output_result,
)

app = typer.Typer(help="Smart recording open APIs (智能录音)")

_LIST_COLUMNS = ["recording_id", "name", "duration(ms)", "state", "convert_state", "summary_state", "create_time"]
_LIST_KEYS = ["recordingId", "name", "duration", "state", "convertState", "summaryState", "createTime"]

_TAG_COLUMNS = ["tag_id", "name", "sort_weight", "create_time"]
_TAG_KEYS = ["tagId", "name", "sortWeight", "createTime"]

_TEMPLATE_COLUMNS = ["template_id", "name", "template_state", "order"]
_TEMPLATE_KEYS = ["templateId", "name", "templateState", "orderNumber"]

_DETAIL_KEYS = (
    "recordingId",
    "name",
    "sn",
    "deviceName",
    "duration",
    "state",
    "convertState",
    "summaryState",
    "chapterState",
    "shared",
    "createTime",
    "modifyTime",
    "tagIds",
    "templateId",
    "recordingMarker",
    "audioId",
    "transcriptionId",
    "summaryId",
    "chaptersId",
    "hasAudio",
    "hasTranscription",
    "hasSummary",
    "hasChapters",
)


def _row(item, keys):
    if not isinstance(item, dict):
        return ["" for _ in keys]
    return ["" if item.get(key) is None else str(item.get(key, "")) for key in keys]


def _cell(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


@app.command("list")
def list_recordings(
    page: int = typer.Option(1, "--page", help="Page number (starts at 1)"),
    page_size: int = typer.Option(20, "--page-size", help="Page size"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List recordings (paged)."""
    result = get_client().fetch_recording_list(page=page, page_size=page_size, user_token=user_token)
    if is_json_output() or not result.success:
        output_result(result)
        return
    output_result(result, fields=["total", "has_more"], title="Recordings")
    output_list(
        result.recordings,
        columns=_LIST_COLUMNS,
        title="Recording Items",
        row_mapper=lambda item: _row(item, _LIST_KEYS),
    )


@app.command("detail")
def recording_detail(
    recording_id: str = typer.Argument(help="Recording open ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a recording's full detail."""
    result = get_client().fetch_recording_detail(recording_id=recording_id, user_token=user_token)
    if is_json_output() or not result.success or not result.recording:
        output_result(result, title="Recording Detail")
        return
    keys = list(_DETAIL_KEYS)
    for key in result.recording:
        if key not in keys:
            keys.append(key)
    table = Table(title="Recording Detail", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    for key in keys:
        table.add_row(key, _cell(result.recording.get(key)))
    console.print(table)


@app.command("transcribe")
def transcribe_recording(
    recording_id: str = typer.Argument(help="Recording open ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm the transcription task before submitting"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without submitting"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Submit an ASR transcription task (high-risk write)."""
    confirm_high_risk("transcribe", f"recording {recording_id}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    result = get_client().create_transcription_task(recording_id=recording_id, user_token=user_token)
    output_result(
        result,
        fields=["recording_id", "convert_state"],
        title="Transcription Task Submitted",
    )


@app.command("summary")
def summarize_recording(
    recording_id: str = typer.Argument(help="Recording open ID"),
    template_id: Optional[str] = typer.Option(None, "--template-id", help="Summary template open ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm the summary task before submitting"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without submitting"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Submit a meeting-summary task (high-risk write)."""
    confirm_high_risk("summarize", f"recording {recording_id}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    result = get_client().create_summary_task(
        recording_id=recording_id, template_id=template_id, user_token=user_token,
    )
    output_result(
        result,
        fields=["recording_id", "summary_state"],
        title="Summary Task Submitted",
    )


@app.command("tags")
def list_tags(
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List the current staff's recording tags."""
    result = get_client().fetch_recording_tags(user_token=user_token)
    if is_json_output() or not result.success:
        output_result(result)
        return
    output_list(
        result.tags,
        columns=_TAG_COLUMNS,
        title="Recording Tags",
        row_mapper=lambda item: _row(item, _TAG_KEYS),
    )


@app.command("templates")
def list_templates(
    page: int = typer.Option(1, "--page", help="Page number (starts at 1)"),
    page_size: int = typer.Option(20, "--page-size", help="Page size"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List summary templates visible to the organization (paged)."""
    result = get_client().fetch_recording_templates(page=page, page_size=page_size, user_token=user_token)
    if is_json_output() or not result.success:
        output_result(result)
        return
    output_result(result, fields=["total", "has_more"], title="Recording Templates")
    output_list(
        result.templates,
        columns=_TEMPLATE_COLUMNS,
        title="Template Items",
        row_mapper=lambda item: _row(item, _TEMPLATE_KEYS),
    )
