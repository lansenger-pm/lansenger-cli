import typer
import json
from typing import List

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Calendar and schedule operations")


@app.command("primary")
def fetch_primary_calendar(
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Fetch primary calendar"""
    client = get_client()
    result = client.fetch_primary_calendar(user_token=user_token, user_id=user_id)
    output_result(result, fields=[
        "calendar_id", "summary", "description", "permissions", "role",
    ], title="Primary Calendar")


@app.command("create-schedule")
def create_schedule(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    summary: str = typer.Argument(help="Schedule summary/title"),
    start_time: int = typer.Argument(help="Start time (unix timestamp in seconds)"),
    end_time: int = typer.Argument(help="End time (unix timestamp in seconds)"),
    attendees: str = typer.Argument(help="Attendees as JSON list: '[{\"staffId\":\"xxx\",\"attendeeFlag\":\"yes\"}]'"),
    description: str = typer.Option("", "--desc", "-d", help="Schedule description"),
    all_day: str = typer.Option("no", "--all-day", help="yes or no"),
    date: str = typer.Option("", "--date", help="Date string for allDay=yes, e.g. 2026-01-01"),
    repeat_type: str = typer.Option("no", "--repeat", help="Repeat type: no, daily, weekly, monthly, yearly, work_day, custom"),
    reminder_type: str = typer.Option("yes", "--reminder", help="Reminder type: yes or no"),
    time_zone: str = typer.Option("Asia/Shanghai", "--tz", help="Time zone, e.g. Asia/Shanghai"),
    rule: str = typer.Option("", "--rule", help="RFC 5545 repeat rule JSON (for custom repeat)"),
    expire: str = typer.Option("", "--expire", help="Expire date type: yes or no"),
    attendee_perms: str = typer.Option("", "--attendee-perms", help="Attendee permissions: can_modify, can_invite, can_see, none"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Create a schedule in calendar"""
    client = get_client()
    attendees_list = json.loads(attendees)
    start_time_dict = {"time": start_time, "date": date, "timeZone": time_zone}
    end_time_dict = {"time": end_time, "date": date, "timeZone": time_zone}
    if all_day == "yes":
        start_time_dict["timeZone"] = "UTC"
        end_time_dict["timeZone"] = "UTC"
    result = client.create_schedule(
        calendar_id=calendar_id, summary=summary,
        start_time=start_time_dict, end_time=end_time_dict,
        attendees=attendees_list, description=description,
        all_day=all_day, repeat_type=repeat_type,
        reminder_type=reminder_type,
        rule=rule, expire_date_type=expire, attendee_permissions=attendee_perms,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Create Schedule Result")


@app.command("fetch-schedule")
def fetch_schedule(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Fetch schedule details"""
    client = get_client()
    result = client.fetch_schedule(
        calendar_id=calendar_id, schedule_id=schedule_id,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=[
        "schedule_id", "summary", "description", "all_day",
        "start_time", "end_time", "creator", "rsvp_status",
    ], title="Schedule Info")


@app.command("delete-schedule")
def delete_schedule(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Delete a schedule"""
    client = get_client()
    result = client.delete_schedule(
        calendar_id=calendar_id, schedule_id=schedule_id,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Delete Schedule Result")


@app.command("list-schedules")
def fetch_schedule_list(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    start_time: int = typer.Argument(help="Start time (unix timestamp in seconds)"),
    end_time: int = typer.Argument(help="End time (unix timestamp in seconds)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """List schedules in a calendar"""
    client = get_client()
    result = client.fetch_schedule_list(
        calendar_id=calendar_id, start_time=start_time, end_time=end_time,
        user_token=user_token, user_id=user_id,
    )
    if result.success and result.schedule_list:
        output_list(result.schedule_list, columns=["Schedule ID", "Summary"], row_mapper=lambda s: [
            s.get("scheduleId", ""), s.get("summary", ""),
        ])
    else:
        output_result(result, title="Schedule List")


@app.command("attendees")
def fetch_schedule_attendees(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(500, "--size", "-s", help="Page size"),
):
    """Fetch schedule attendees"""
    client = get_client()
    result = client.fetch_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        user_token=user_token, user_id=user_id,
        page=page, page_size=page_size,
    )
    output_result(result, fields=["total"], title="Schedule Attendees")


@app.command("add-attendees")
def add_schedule_attendees(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    attendees: str = typer.Argument(help="Attendee staff IDs as JSON list: '[\"id1\",\"id2\"]'"),
    reminder_type: str = typer.Option("", "--reminder", help="Reminder type: yes or no"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Add attendees to a schedule"""
    client = get_client()
    attendees_list = json.loads(attendees)
    result = client.add_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        attendees=attendees_list, reminder_type=reminder_type,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Add Attendees Result")


@app.command("delete-attendees")
def delete_schedule_attendees(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    attendees: str = typer.Argument(help="Attendee staff IDs as JSON list"),
    reminder_type: str = typer.Option("", "--reminder", help="Reminder type: yes or no"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Delete attendees from a schedule"""
    client = get_client()
    attendees_list = json.loads(attendees)
    result = client.delete_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        attendees=attendees_list, reminder_type=reminder_type,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Delete Attendees Result")


@app.command("update-schedule")
def update_schedule(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    summary: str = typer.Option("", "--summary", help="New schedule summary"),
    description: str = typer.Option("", "--desc", "-d", help="New description"),
    operation_type: str = typer.Option("modify_all", "--op", help="Operation type: modify_all, modify_current, modify_current_after"),
    current_time: int = typer.Option(0, "--current-time", help="Required when op != modify_all"),
    reminder_type: str = typer.Option("", "--reminder", help="Reminder type: yes or no"),
    repeat_type: str = typer.Option("", "--repeat", help="Repeat type: no, day, week, month, year, work_day, custom"),
    rule: str = typer.Option("", "--rule", help="RFC 5545 repeat rule"),
    expire_date_type: str = typer.Option("", "--expire", help="Expire date type: yes or no"),
    all_day: str = typer.Option("", "--all-day", help="All day: yes or no"),
    attendee_permissions: str = typer.Option("", "--permissions", help="Attendee permissions: can_modify, can_invite, can_see, none"),
    start_time: str = typer.Option("", "--start-time", help="Start time as JSON dict: {\"time\":..., \"date\":..., \"timeZone\":...}"),
    end_time: str = typer.Option("", "--end-time", help="End time as JSON dict"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Update schedule details"""
    client = get_client()
    start_time_dict = json.loads(start_time) if start_time else None
    end_time_dict = json.loads(end_time) if end_time else None
    result = client.update_schedule(
        calendar_id=calendar_id, schedule_id=schedule_id,
        summary=summary or None, description=description or None,
        operation_type=operation_type, current_time=current_time or None,
        reminder_type=reminder_type or None,
        repeat_type=repeat_type or None, rule=rule or None,
        expire_date_type=expire_date_type or None,
        all_day=all_day or None,
        attendee_permissions=attendee_permissions or None,
        start_time=start_time_dict, end_time=end_time_dict,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_ids"], title="Update Schedule Result")


@app.command("attendee-meta")
def update_schedule_attendee_meta(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    rsvp_status: str = typer.Option("", "--rsvp", help="RSVP status: accept, tentative, decline"),
    color: str = typer.Option("", "--color", help="Hex color (e.g. #FF347AFC)"),
    permissions: str = typer.Option("", "--permissions", help="Visibility: private, public, default"),
    busy_free_state: str = typer.Option("", "--busy-free", help="Busy/free state: busy, free"),
    remind_times: str = typer.Option("", "--remind-times", help="Reminder offsets in minutes as JSON list, e.g. '[5,15]'"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Update attendee meta information"""
    client = get_client()
    remind_times_list = json.loads(remind_times) if remind_times else None
    result = client.update_schedule_attendee_meta(
        calendar_id=calendar_id, schedule_id=schedule_id,
        rsvp_status=rsvp_status or None, color=color or None,
        permissions=permissions or None,
        busy_free_state=busy_free_state or None,
        remind_times=remind_times_list,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, title="Update Attendee Meta Result")


@app.command("update-attendees")
def update_schedule_attendees(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    add_attendees: str = typer.Option("", "--add", "-A", help="Staff IDs to add as JSON list: '[\"id1\",\"id2\"]'"),
    delete_attendees: str = typer.Option("", "--remove", "-X", help="Staff IDs to remove as JSON list"),
    reminder_type: str = typer.Option("", "--reminder", help="Reminder type: yes or no"),
    operation_type: str = typer.Option("", "--op", help="Operation: modify_current, modify_current_after, modify_all"),
    current_time: int = typer.Option(0, "--current-time", help="Required when op != modify_all"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    """Batch add and/or delete schedule attendees (4.23.19)"""
    client = get_client()
    add_list = json.loads(add_attendees) if add_attendees else None
    del_list = json.loads(delete_attendees) if delete_attendees else None
    result = client.update_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        add_attendees=add_list, delete_attendees=del_list,
        reminder_type=reminder_type or None,
        operation_type=operation_type or None,
        current_time=current_time or None,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_ids", "failed_attendees"], title="Update Attendees Result")