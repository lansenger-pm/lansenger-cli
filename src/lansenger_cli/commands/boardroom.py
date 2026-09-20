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

app = typer.Typer(help="Meeting-room reservation (会议室预定 V2)")


def _print_page_items(items, columns, row_mapper=None, title="Result"):
    if not items or is_json_output():
        return

    def safe_mapper(item):
        mapper = row_mapper or (lambda i: [i.get(c, "") for c in columns])
        return [str(v) if v is not None else "" for v in mapper(item)]

    output_list(items, columns=columns, title=title, row_mapper=safe_mapper)


@app.command("rooms")
def rooms(
    grading_id: str = typer.Option("", "--grading-id", help="Grading (分区) ID"),
    area_office_id: str = typer.Option("", "--area-office-id", help="Office area ID"),
    floor_ids: str = typer.Option("", "--floor-ids", help="Comma-separated floor IDs"),
    equipment: str = typer.Option("", "--equipment", help="Comma-separated equipment list"),
    time_start: str = typer.Option("", "--time-start", help="Filter start (yyyy-MM-dd HH:mm)"),
    time_end: str = typer.Option("", "--time-end", help="Filter end (yyyy-MM-dd HH:mm)"),
    query_date: str = typer.Option("", "--date", help="Query date (yyyy-MM-dd, enables deactivation info)"),
    page: int = typer.Option(1, "--page", help="Page number"),
    limit: int = typer.Option(10, "--size", help="Page size"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Filter meeting rooms (paged)"""
    client = get_client()
    result = client.fetch_boardroom_list(
        grading_id=grading_id, area_office_id=area_office_id,
        floor_ids=[f.strip() for f in floor_ids.split(",") if f.strip()] or None,
        equipment=[e.strip() for e in equipment.split(",") if e.strip()] or None,
        reserve_time_start=time_start, reserve_time_end=time_end,
        query_date=query_date, page=page, limit=limit, user_token=user_token,
    )
    output_result(result, fields=["count"], title="Boardroom List")
    _print_page_items(
        result.items, ["id", "name", "areaName", "areaOfficeFoolerName", "peopleNum"],
        row_mapper=lambda i: [i.get("id", ""), i.get("name", ""), i.get("areaName", ""),
                              i.get("areaOfficeFoolerName", ""), i.get("peopleNum", "")],
        title="Meeting Rooms",
    )


@app.command("room-detail")
def room_detail(
    room_id: str = typer.Argument(help="Meeting-room ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch meeting-room detail (equipment, service staff)"""
    client = get_client()
    result = client.fetch_boardroom_detail(room_id, user_token=user_token)
    output_result(
        result,
        fields=["room_id", "name", "status", "people_num", "can_reserve_flag", "area_name", "address"],
        title="Boardroom Detail",
    )


@app.command("schedule")
def schedule(
    room_id: str = typer.Argument(help="Meeting-room ID"),
    query_date: str = typer.Argument(help="Query date (yyyy-MM-dd)"),
    grading_id: str = typer.Option(..., "--grading-id", help="Grading (分区) ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a room's bookings + deactivation info for a date"""
    client = get_client()
    result = client.fetch_boardroom_schedule(room_id, query_date, grading_id, user_token=user_token)
    output_result(
        result,
        fields=["room_id", "name", "people_num", "can_reserve_flag", "reserves", "deactivations"],
        title="Room Schedule",
    )


@app.command("reserve-detail")
def reserve_detail(
    reserve_room_id: str = typer.Argument(help="Reservation ID"),
    grading_id: str = typer.Option("", "--grading-id", help="Grading (分区) ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch reservation detail (attendees, approval flow in raw JSON)"""
    client = get_client()
    result = client.fetch_boardroom_reserve_detail(reserve_room_id, grading_id=grading_id, user_token=user_token)
    output_result(
        result,
        fields=["reserve_id", "boardroom_name", "meeting_name", "status", "reserve_time_start",
                "reserve_time_end", "reserve_user_name", "people_number"],
        title="Reserve Detail",
    )


@app.command("reserve")
def reserve(
    boardroom_id: str = typer.Argument(help="Meeting-room ID"),
    name: str = typer.Argument(help="Meeting name"),
    grading_id: str = typer.Option(..., "--grading-id", help="Grading (分区) ID"),
    start: str = typer.Option(..., "--start", help="Reserve start (yyyy-MM-dd HH:mm:ss)"),
    end: str = typer.Option(..., "--end", help="Reserve end (yyyy-MM-dd HH:mm:ss)"),
    notice_time: str = typer.Option(..., "--notice-time", help="Meeting reminder: 不提醒/立即提醒/会前15分钟/会前30分钟/会前1小时/会前2小时/会前1天"),
    people_number: str = typer.Option("", "--people", help="Attendee count"),
    toastmaster: str = typer.Option("", "--toastmaster", help="Host (max 10 chars)"),
    leader: str = typer.Option("", "--leader", help="Attending leader (max 200 chars)"),
    is_video: str = typer.Option("", "--is-video", help="Video meeting: 0=on, 1=off (doc default 1)"),
    video_name: str = typer.Option("", "--video-name", help="Video meeting name"),
    invitation_users: str = typer.Option("", "--invite", help="Comma-separated attendee staff IDs"),
    approve_users: str = typer.Option("", "--approvers", help="Comma-separated approver staff IDs"),
    reserve_type: str = typer.Option("0", "--reserve-type", help="0=single, 1=repeat"),
    repeat_type: str = typer.Option("", "--repeat-type", help="day/week/month (reserve-type=1)"),
    repeat_days: str = typer.Option("", "--repeat-days", help="Comma-separated repeat day numbers"),
    skip: str = typer.Option("", "--skip", help="Skip weekends/holidays: 0=skip, 1=don't"),
    repeat_end: str = typer.Option("", "--repeat-end", help="Repeat end (yyyy-MM-dd HH:mm:ss)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Reserve a meeting room (single or repeating)"""
    client = get_client()
    result = client.reserve_boardroom(
        boardroom_id, name, grading_id, start, end, notice_time,
        people_number=people_number, toastmaster=toastmaster, leader=leader,
        is_video=is_video, video_name=video_name,
        invitation_user_list=[u.strip() for u in invitation_users.split(",") if u.strip()] or None,
        user_list=[u.strip() for u in approve_users.split(",") if u.strip()] or None,
        reserve_type=reserve_type, repeat_type=repeat_type,
        repeat_days=[int(d) for d in repeat_days.split(",") if d.strip()] or None,
        skip=skip, repeat_end_date=repeat_end, user_token=user_token,
    )
    output_result(
        result,
        fields=["reserve_id", "reserve_code", "boardroom_name", "meeting_name", "status", "reserve_time"],
        title="Reserve Result",
    )


@app.command("edit-reserve")
def edit_reserve(
    reserve_id: str = typer.Argument(help="Reservation ID"),
    boardroom_id: str = typer.Argument(help="Meeting-room ID"),
    name: str = typer.Argument(help="Meeting name"),
    grading_id: str = typer.Option(..., "--grading-id", help="Grading (分区) ID"),
    start: str = typer.Option(..., "--start", help="Reserve start (yyyy-MM-dd HH:mm:ss)"),
    end: str = typer.Option(..., "--end", help="Reserve end (yyyy-MM-dd HH:mm:ss)"),
    notice_time: str = typer.Option(..., "--notice-time", help="Meeting reminder"),
    edit_type: str = typer.Option("1", "--edit-type", help="1=this booking, 2=this and following"),
    people_number: str = typer.Option("", "--people", help="Attendee count"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Edit a reservation (only non-approval-flow bookings)"""
    client = get_client()
    result = client.edit_boardroom_reserve(
        reserve_id, boardroom_id, name, grading_id, start, end, notice_time,
        edit_type=edit_type, people_number=people_number, user_token=user_token,
    )
    output_result(
        result,
        fields=["reserve_id", "reserve_code", "meeting_name", "status", "reserve_time"],
        title="Edit Reserve Result",
    )


@app.command("cancel")
def cancel(
    reserve_id: str = typer.Argument(help="Reservation ID"),
    reason: str = typer.Option("", "--reason", help="Cancel reason (max 200 chars)"),
    cancel_type: str = typer.Option("", "--cancel-type", help="1=this, 2=this and following, 3=all unfinished"),
    is_send: Optional[bool] = typer.Option(None, "--notify", help="Notify attendees"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm cancellation before executing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without cancelling"),
):
    """Cancel a reservation (status 0/1/5 only)"""
    confirm_high_risk("cancel", f"reservation {reserve_id}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    client = get_client()
    result = client.cancel_boardroom_reserve(
        reserve_id, cancel_reason=reason, is_send=is_send, cancel_type=cancel_type,
        user_token=user_token,
    )
    output_result(result, fields=["done"], title="Cancel Result")


@app.command("confirm-sign")
def confirm_sign(
    reserve_id: str = typer.Argument(help="Reservation ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Scan-code confirmation (status 1 only)"""
    client = get_client()
    result = client.confirm_boardroom_sign(reserve_id, user_token=user_token)
    output_result(result, fields=["done"], title="Confirm Sign Result")


@app.command("my-reserves")
def my_reserves(
    grading_id: str = typer.Option(..., "--grading-id", help="Grading (分区) ID"),
    keys: str = typer.Option("", "--keys", help="Keyword search"),
    start_time: str = typer.Option("", "--start-time", help="Reserve start filter"),
    end_time: str = typer.Option("", "--end-time", help="Reserve end filter"),
    boardroom_id: str = typer.Option("", "--room-id", help="Meeting-room ID"),
    page: int = typer.Option(1, "--page", help="Page number"),
    limit: int = typer.Option(10, "--size", help="Page size"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page my reservations with filters"""
    client = get_client()
    result = client.fetch_my_boardroom_reserves(
        grading_id, keys=keys, start_time=start_time, end_time=end_time,
        boardroom_id=boardroom_id, page=page, limit=limit, user_token=user_token,
    )
    output_result(result, fields=["count"], title="My Reservations")
    _print_page_items(
        result.items, ["id", "reserveCode", "boardRoomName", "name", "status"],
        row_mapper=lambda i: [i.get("id", ""), i.get("reserveCode", ""), i.get("boardRoomName", ""),
                              i.get("name", ""), i.get("status", "")],
        title="Reservations",
    )


@app.command("gradings")
def gradings(
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch gradings visible to the user (gradingId source)"""
    client = get_client()
    result = client.fetch_boardroom_gradings(user_token=user_token)
    output_result(result, fields=["total"], title="Boardroom Gradings")
    _print_page_items(
        result.gradings, ["id", "name", "type"],
        row_mapper=lambda g: [g.get("id", ""), g.get("name", ""), g.get("type", "")],
        title="Gradings",
    )


@app.command("area-offices")
def area_offices(
    grading_id: str = typer.Argument(help="Grading (分区) ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch office areas under a grading"""
    client = get_client()
    result = client.fetch_boardroom_area_offices(grading_id, user_token=user_token)
    output_result(result, fields=["total"], title="Office Areas")
    _print_page_items(
        result.areas, ["id", "cityName", "areaName"],
        row_mapper=lambda a: [a.get("id", ""), a.get("cityName", ""), a.get("areaName", "")],
        title="Office Areas",
    )
