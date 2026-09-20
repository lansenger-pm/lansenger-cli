import json
from typing import Optional

import typer

from lansenger_cli.utils import (
    confirm_high_risk,
    get_client,
    is_json_output,
    output_list,
    output_result,
)

from lansenger_sdk.videoconferences import VC_FETCH_RANGE_PERSON, VC_OPS

app = typer.Typer(help="Videoconference open APIs (视频会议开放能力)")


def _json_list(value: str, name: str) -> list:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{name} must be valid JSON") from exc
    if not isinstance(parsed, list):
        raise typer.BadParameter(f"{name} must be a JSON list")
    return parsed


def _require_members_with_host(members: list):
    hosts = [m for m in members if str(m.get("role", "")) == "admin"]
    if len(hosts) != 1:
        raise typer.BadParameter(
            "exactly one member must have role='admin' (主持人)"
        )


def _print_page_items(items, columns=None, row_mapper=None, title="Result"):
    if not items or is_json_output():
        return
    if columns is None:
        columns = list(items[0].keys())
        return

    def safe_mapper(item):
        mapper = row_mapper or (lambda i: [i.get(c, "") for c in columns])
        return [str(v) if v is not None else "" for v in mapper(item)]

    output_list(items, columns=columns, title=title, row_mapper=safe_mapper)


@app.command("create")
def create_meeting(
    subject: str = typer.Argument(help="Meeting subject"),
    org_id: str = typer.Argument(help="Organization ID"),
    start_time: int = typer.Option(..., "--start-time", help="Start time in epoch milliseconds"),
    member: str = typer.Option(..., "--member", help='JSON list: \'[{"staffId":"u1","employeeName":"A","role":"admin"}]\' — exactly one role="admin"'),
    auto_record: int = typer.Option(0, "--auto-record", help="Auto record: 0=no, 1=yes"),
    type: int = typer.Option(1, "--type", help="Meeting type: 0=instant, 1=reserved"),
    group_new: int = typer.Option(0, "--group-new", help="Auto-create group: 0=no, 1=yes"),
    conf_password: str = typer.Option("", "--conf-password", help="Meeting password"),
    control_password: str = typer.Option("", "--control-password", help="Host-control password"),
    mask_type: int = typer.Option(0, "--mask-type", help="Mask type"),
    ext_attr: str = typer.Option("", "--ext-attr", help="Extension attributes"),
    join_mute: Optional[int] = typer.Option(None, "--join-mute", help="Join muted (PRS >=3.7)"),
    open_mute: Optional[int] = typer.Option(None, "--open-mute", help="Start muted (PRS >=3.7)"),
    enable_pre_join: Optional[int] = typer.Option(None, "--enable-pre-join", help="Pre-join lobby (PRS >=3.7)"),
    user_stop_time: Optional[int] = typer.Option(None, "--user-stop-time", help="Auto-stop time in epoch milliseconds (PRS >=3.8)"),
    invite_admin: Optional[int] = typer.Option(None, "--invite-admin", help="Invite host on create (PRS >=3.8)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Create a meeting (instant or reserved)."""
    members = _json_list(member, "--member")
    _require_members_with_host(members)
    result = get_client().create_meeting(
        subject=subject, start_time=start_time, members=members, org_id=org_id,
        auto_record=auto_record, type=type, group_new=group_new,
        conf_password=conf_password, control_password=control_password,
        mask_type=mask_type, ext_attr=ext_attr, join_mute=join_mute,
        open_mute=open_mute, enable_pre_join=enable_pre_join,
        user_stop_time=user_stop_time, invite_admin=invite_admin,
        user_token=user_token,
    )
    output_result(
        result,
        fields=["mid", "subject", "meeting_number", "start_time", "type", "status"],
        title="Meeting Created",
    )


@app.command("modify")
def modify_meeting(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    subject: str = typer.Option(..., "--subject", help="Meeting subject"),
    start_time: int = typer.Option(..., "--start-time", help="Start time in epoch milliseconds"),
    member: str = typer.Option(..., "--member", help='JSON list: \'[{"staffId":"u1","employeeName":"A","role":"admin"}]\' — exactly one role="admin"'),
    auto_record: int = typer.Option(0, "--auto-record", help="Auto record: 0=no, 1=yes"),
    type: int = typer.Option(1, "--type", help="Meeting type: 0=instant, 1=reserved"),
    group_new: int = typer.Option(0, "--group-new", help="Auto-create group: 0=no, 1=yes"),
    conf_password: str = typer.Option("", "--conf-password", help="Meeting password (omit to keep)"),
    control_password: str = typer.Option("", "--control-password", help="Host-control password (omit to keep)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Modify a meeting that has not started."""
    members = _json_list(member, "--member")
    _require_members_with_host(members)
    result = get_client().modify_meeting(
        mid=mid, subject=subject, start_time=start_time, members=members,
        org_id=org_id, operator=operator, auto_record=auto_record, type=type,
        group_new=group_new, conf_password=conf_password,
        control_password=control_password, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Meeting Modified")


@app.command("cancel")
def cancel_meeting(
    mid: int = typer.Argument(help="Meeting ID (must not have started)"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm cancellation before executing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without cancelling"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Cancel a meeting that has not started (cancel only applies before start)."""
    confirm_high_risk("cancel", f"meeting {mid}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    result = get_client().cancel_meeting(
        mid=mid, org_id=org_id, operator=operator, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Meeting Cancelled")


@app.command("stop")
def stop_meeting(
    mid: int = typer.Argument(help="Meeting ID (running meeting)"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm stopping before executing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without stopping"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Stop (end) a running meeting."""
    confirm_high_risk("stop", f"meeting {mid}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    result = get_client().stop_meeting(
        mid=mid, org_id=org_id, operator=operator, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Meeting Stopped")


@app.command("detail")
def meeting_detail(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch meeting detail by mid."""
    result = get_client().fetch_meeting_detail(
        mid=mid, org_id=org_id, operator=operator, user_token=user_token,
    )
    output_result(
        result,
        fields=["mid", "subject", "meeting_number", "start_time", "stop_time", "type", "status", "admin"],
        title="Meeting Detail",
    )


@app.command("list")
def meeting_list(
    org_id: str = typer.Argument(help="Organization ID"),
    start_time: int = typer.Option(..., "--start-time", help="Range start in epoch milliseconds"),
    end_time: int = typer.Option(..., "--end-time", help="Range end in epoch milliseconds"),
    fetch_range: str = typer.Option("all", "--fetch-range", help="Range scope: my, all, person"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID (required when --fetch-range=person)"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List meetings by time range."""
    if fetch_range == VC_FETCH_RANGE_PERSON and not staff_id:
        raise typer.BadParameter("--staff-id is required when --fetch-range=person")
    result = get_client().fetch_meeting_list(
        org_id=org_id, start_time=start_time, end_time=end_time,
        fetch_range=fetch_range, staff_id=staff_id,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Meetings")
    _print_page_items(result.items, ["id", "subject", "status", "startTime"],
                      title="Meeting Items")


@app.command("record-list")
def meeting_record_list(
    org_id: str = typer.Argument(help="Organization ID"),
    start_time: int = typer.Option(..., "--start-time", help="Range start in epoch milliseconds"),
    end_time: int = typer.Option(..., "--end-time", help="Range end in epoch milliseconds"),
    admin: str = typer.Option("", "--admin", help="Filter by host staff ID"),
    create_source: int = typer.Option(0, "--create-source", help="0=platform client, 1=third-party app"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List meeting operation records."""
    result = get_client().fetch_meeting_record_list(
        org_id=org_id, start_time=start_time, end_time=end_time,
        admin=admin, create_source=create_source,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Meeting Records")
    _print_page_items(result.items, title="Record Items")


@app.command("simplerecord")
def member_simplerecord(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List member join/leave records of a meeting."""
    result = get_client().fetch_member_simplerecord(
        mid=mid, org_id=org_id, operator=operator,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Member Records")
    _print_page_items(result.items, title="Member Record Items")


@app.command("fixroom-list")
def fixroom_list(
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List fixed (cloud) meeting rooms."""
    result = get_client().fetch_fixroom_list(
        org_id=org_id, operator=operator,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Fixroom List")
    _print_page_items(result.items, title="Fixroom Items")


@app.command("status")
def meeting_status(
    org_id: str = typer.Argument(help="Organization ID"),
    mids: str = typer.Option(..., "--mids", help="Comma-separated meeting IDs"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Batch-fetch meeting status by mids."""
    mid_list = [m.strip() for m in mids.split(",") if m.strip()]
    if not mid_list:
        raise typer.BadParameter("--mids must contain at least one meeting ID")
    result = get_client().fetch_meeting_status(
        mids=mid_list, org_id=org_id, user_token=user_token,
    )
    output_result(result, title="Meeting Status")
    _print_page_items(result.statuses, title="Status Items")


@app.command("subscribe")
def subscribe_meeting_events(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    events: str = typer.Option(..., "--events", help='JSON list of event definitions, e.g. \'[{"eventType":1,"callBackUrl":"https://..."}]\''),
    call_back_info: str = typer.Option("", "--call-back-info", help="Optional callback info"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Subscribe meeting status-change events."""
    event_list = _json_list(events, "--events")
    result = get_client().subscribe_meeting_events(
        mid=mid, org_id=org_id, events=event_list,
        call_back_info=call_back_info, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Events Subscribed")


@app.command("params")
def meeting_params(
    meeting_number: str = typer.Argument(help="Meeting number"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch meeting params by meetingNumber (PRS >=3.8)."""
    result = get_client().fetch_meeting_params(
        meeting_number=meeting_number, org_id=org_id, operator=operator,
        user_token=user_token,
    )
    output_result(result, title="Meeting Params")


@app.command("history")
def history_meetings(
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a person's past meetings (paged)."""
    result = get_client().fetch_history_meetings(
        org_id=org_id, operator=operator,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="History Meetings")
    _print_page_items(result.items, title="History Items")


@app.command("active")
def active_meetings(
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a person's running + reserved meetings (paged)."""
    result = get_client().fetch_active_meetings(
        org_id=org_id, operator=operator,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Active Meetings")
    _print_page_items(result.items, title="Active Items")


@app.command("member-control")
def member_control(
    mid: int = typer.Argument(help="Meeting ID"),
    staff_id: str = typer.Argument(help="Staff ID the operation applies to"),
    op_code: str = typer.Argument(help="Operation code (kick/join/handup/muteall/setHost/...)"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Host controls a member (opCode operation)."""
    if op_code not in VC_OPS:
        raise typer.BadParameter(f"op-code must be one of {', '.join(VC_OPS)}")
    result = get_client().control_member(
        mid=mid, staff_id=staff_id, op_code=op_code, operator=operator,
        org_id=org_id, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Member Controlled")


@app.command("invite")
def invite_members(
    meeting_number: str = typer.Argument(help="Meeting number (running meeting)"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    member: str = typer.Option(..., "--member", help='JSON list: \'[{"staffId":"u1","employeeName":"A","type":0,"video":1,"audio":1}]\''),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Invite members to a running meeting."""
    members = _json_list(member, "--member")
    if not members:
        raise typer.BadParameter("--member must contain at least one entry")
    result = get_client().invite_members(
        meeting_number=meeting_number, members=members, org_id=org_id,
        operator=operator, user_token=user_token,
    )
    output_result(result, fields=["done", "message"], title="Members Invited")


@app.command("member-list")
def member_list(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    limit: int = typer.Option(10, "--limit", help="Page size"),
    offset: int = typer.Option(0, "--offset", help="Page offset"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List members of a meeting (paged)."""
    result = get_client().fetch_member_list(
        mid=mid, org_id=org_id, operator=operator,
        limit=limit, offset=offset, user_token=user_token,
    )
    output_result(result, fields=["offset", "total"], title="Member List")
    _print_page_items(result.items, title="Member Items")


@app.command("vod-list")
def vod_list(
    mid: int = typer.Argument(help="Meeting ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List recordings of a meeting."""
    result = get_client().fetch_vod_list(
        mid=mid, org_id=org_id, operator=operator, user_token=user_token,
    )
    output_result(result, title="Vod List")
    _print_page_items(result.items, title="Vod Items")


@app.command("vod-download")
def vod_download_urls(
    org_id: str = typer.Argument(help="Organization ID"),
    operator: str = typer.Argument(help="Operator staff ID"),
    vods: str = typer.Option(..., "--vods", help='JSON list of \'{"vodId":"..."}\' entries — max 3 per call'),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch recording download URLs (max 3 vods per call)."""
    vod_entries = _json_list(vods, "--vods")
    if not vod_entries or len(vod_entries) > 3:
        raise typer.BadParameter("--vods must contain 1..3 entries")
    result = get_client().fetch_vod_download_urls(
        vods=vod_entries, org_id=org_id, operator=operator,
        user_token=user_token,
    )
    output_result(result, title="Vod Download URLs")


@app.command("org-conf")
def org_conf(
    org_id: str = typer.Argument(help="Organization ID"),
    meeting_number: str = typer.Option("", "--meeting-number", help="Fetch the config of the org owning this meeting (PRS >=3.8)"),
    operator: str = typer.Option("", "--operator", help="Operator staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch org videoconference config (PRS >=3.8)."""
    result = get_client().fetch_org_videoconference_conf(
        org_id=org_id, meeting_number=meeting_number, operator=operator,
        user_token=user_token,
    )
    output_result(
        result,
        fields=["max_person", "default_max_person", "allowed_record_flag", "force_passwd_flag", "space_size"],
        title="Org Videoconference Config",
    )
