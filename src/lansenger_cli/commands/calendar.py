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
    client = get_client()
    result = client.fetch_primary_calendar(user_token=user_token, user_id=user_id)
    output_result(result, fields=[
        "calendar_id", "summary", "description", "permissions", "role",
    ], title="Primary Calendar")


@app.command("create-schedule")
def create_schedule(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    summary: str = typer.Argument(help="Schedule summary/title"),
    start_time: str = typer.Argument(help="Start time as JSON: '{\"dateTime\":\"2026-01-01T09:00:00\",\"timeZone\":\"Asia/Shanghai\"}'"),
    end_time: str = typer.Argument(help="End time as JSON"),
    attendees: str = typer.Argument(help="Attendees as JSON list: '[{\"staffId\":\"xxx\"}]'"),
    description: str = typer.Option("", "--desc", "-d", help="Schedule description"),
    all_day: str = typer.Option("no", "--all-day", help="yes or no"),
    repeat_type: str = typer.Option("no", "--repeat", help="Repeat type: no, daily, weekly, monthly, yearly"),
    reminder_type: str = typer.Option("yes", "--reminder", help="Reminder type: yes or no"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    client = get_client()
    start_time_dict = json.loads(start_time)
    end_time_dict = json.loads(end_time)
    attendees_list = json.loads(attendees)
    result = client.create_schedule(
        calendar_id=calendar_id, summary=summary,
        start_time=start_time_dict, end_time=end_time_dict,
        attendees=attendees_list, description=description,
        all_day=all_day, repeat_type=repeat_type,
        reminder_type=reminder_type,
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
    client = get_client()
    result = client.delete_schedule(
        calendar_id=calendar_id, schedule_id=schedule_id,
        user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Delete Schedule Result")


@app.command("list-schedules")
def fetch_schedule_list(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    start_time: int = typer.Argument(help="Start time (unix timestamp)"),
    end_time: int = typer.Argument(help="End time (unix timestamp)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    client = get_client()
    result = client.fetch_schedule_list(
        calendar_id=calendar_id, start_time=start_time, end_time=end_time,
        user_token=user_token, user_id=user_id,
    )
    if result.success and result.schedule_list:
        output_list(result.schedule_list, columns=["Schedule ID", "Summary"], row_mapper=lambda s: [
            getattr(s, "schedule_id", ""), getattr(s, "summary", ""),
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
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    client = get_client()
    attendees_list = json.loads(attendees)
    result = client.add_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        attendees=attendees_list, user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Add Attendees Result")


@app.command("delete-attendees")
def delete_schedule_attendees(
    calendar_id: str = typer.Argument(help="Calendar ID"),
    schedule_id: str = typer.Argument(help="Schedule ID"),
    attendees: str = typer.Argument(help="Attendee staff IDs as JSON list"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    user_id: str = typer.Option("", "--user-id", help="User ID"),
):
    client = get_client()
    attendees_list = json.loads(attendees)
    result = client.delete_schedule_attendees(
        calendar_id=calendar_id, schedule_id=schedule_id,
        attendees=attendees_list, user_token=user_token, user_id=user_id,
    )
    output_result(result, fields=["schedule_id"], title="Delete Attendees Result")