import base64
import json
from pathlib import Path
from typing import Optional

import typer

from lansenger_cli.utils import get_client, is_json_output, output_list, output_result

app = typer.Typer(help="Manage user-owned personal todos (个人待办)")


def _comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _json_list(value: str, name: str) -> list | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{name} must be valid JSON") from exc
    if not isinstance(parsed, list):
        raise typer.BadParameter(f"{name} must be a JSON list")
    return parsed


@app.command("save")
def save_personal_todo(
    subject: str = typer.Argument(help="Todo subject"),
    create_user_id: str = typer.Argument(help="Creator staff ID"),
    org_id: str = typer.Argument(help="Organization ID (required; never inferred from user-token)"),
    appid: str = typer.Argument(help="Application ID"),
    start_time: int = typer.Option(..., "--start-time", help="Start time in epoch milliseconds"),
    due_time: int = typer.Option(..., "--due-time", help="Due time in epoch milliseconds"),
    priority: int = typer.Option(1, "--priority", help="Priority: 0=low, 1=normal, 2=urgent, 3=very urgent"),
    description: str = typer.Option("", "--description", help="Todo description"),
    parent_code: str = typer.Option("", "--parent-code", help="Parent todo code"),
    finish_time: int = typer.Option(0, "--finish-time", help="Finish time in epoch milliseconds"),
    status_tag_no: str = typer.Option("", "--status-tag-no", help="Unfinished status label"),
    status_tag_yes: str = typer.Option("", "--status-tag-yes", help="Finished status label"),
    subscribe_status: Optional[int] = typer.Option(None, "--subscribe-status", help="Subscribe: 1=yes, 0=no"),
    user_code: str = typer.Option("", "--user-code", help="Private-chat executor authorization code"),
    executors: str = typer.Option("", "--executors", help='JSON list: \'[{"staffId":"u1","opt":1}]\''),
    copys: str = typer.Option("", "--copys", help='JSON list of CC users: \'[{"staffId":"u2","opt":1}]\''),
    resources: str = typer.Option("", "--resources", help="JSON list of uploaded resources"),
    reminds: str = typer.Option("", "--reminds", help='JSON list: \'[{"remindTime":1700000000000,"remindType":"app"}]\''),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Create a user-owned personal todo."""
    result = get_client().save_personal_todo(
        subject=subject,
        start_time=start_time,
        due_time=due_time,
        priority=priority,
        create_user_id=create_user_id,
        org_id=org_id,
        appid=appid,
        description=description,
        parent_code=parent_code,
        finish_time=finish_time,
        status_tag_no=status_tag_no,
        status_tag_yes=status_tag_yes,
        subscribe_status=subscribe_status,
        user_code=user_code,
        executors=_json_list(executors, "--executors"),
        copys=_json_list(copys, "--copys"),
        resources=_json_list(resources, "--resources"),
        reminds=_json_list(reminds, "--reminds"),
        user_token=user_token,
    )
    output_result(result, fields=["todo_code"], title="Personal Todo Created")


@app.command("update")
def update_personal_todo(
    todo_code: str = typer.Argument(help="Todo code"),
    org_id: str = typer.Argument(help="Organization ID (sent at request body top level)"),
    update_fields: str = typer.Option(..., "--update-fields", help="Comma-separated fields to update"),
    subject: str = typer.Option("", "--subject", help="New subject"),
    description: str = typer.Option("", "--description", help="New description"),
    start_time: Optional[int] = typer.Option(None, "--start-time", help="New start time"),
    due_time: Optional[int] = typer.Option(None, "--due-time", help="New due time"),
    finish_time: Optional[int] = typer.Option(None, "--finish-time", help="New finish time"),
    priority: Optional[int] = typer.Option(None, "--priority", help="New priority"),
    subscribe_status: Optional[int] = typer.Option(None, "--subscribe-status", help="New subscribe status"),
    create_user_id: str = typer.Option("", "--create-user-id", help="Creator staff ID"),
    appid: str = typer.Option("", "--appid", help="Application ID"),
    executors: str = typer.Option("", "--executors", help="JSON list of executors"),
    copys: str = typer.Option("", "--copys", help="JSON list of CC users"),
    resources: str = typer.Option("", "--resources", help="JSON list of resources"),
    reminds: str = typer.Option("", "--reminds", help="JSON list of reminders"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Update selected fields of a personal todo."""
    fields = _comma_list(update_fields)
    result = get_client().update_personal_todo(
        todo_code=todo_code,
        org_id=org_id,
        update_fields=fields,
        subject=subject,
        description=description,
        start_time=start_time,
        due_time=due_time,
        finish_time=finish_time,
        priority=priority,
        subscribe_status=subscribe_status,
        create_user_id=create_user_id,
        appid=appid,
        executors=_json_list(executors, "--executors"),
        copys=_json_list(copys, "--copys"),
        resources=_json_list(resources, "--resources"),
        reminds=_json_list(reminds, "--reminds"),
        user_token=user_token,
    )
    output_result(result, fields=["todo_code"], title="Personal Todo Updated")


@app.command("list")
def list_personal_todos(
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Argument(help="Executor staff ID"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    status: Optional[int] = typer.Option(None, "--status", help="0=unfinished, 1=finished; omit for all"),
    app_id: str = typer.Option("", "--app-id", help="Filter by application ID"),
    app_category_name: str = typer.Option("", "--app-category-name", help="Filter by application category"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page a user's personal todos."""
    result = get_client().fetch_personal_todo_list(
        org_id=org_id,
        staff_id=staff_id,
        page_no=page,
        page_size=size,
        status=status,
        app_id=app_id,
        app_category_name=app_category_name,
        user_token=user_token,
    )
    output_result(
        result,
        fields=["page_no", "page_size", "pages", "total", "has_more"],
        title="Personal Todos",
    )
    if result.items and not is_json_output():
        output_list(
            result.items,
            columns=["taskCode", "summarySubject", "status", "startTime", "dueTime"],
            title="Personal Todo Items",
            row_mapper=lambda item: [
                str(item.get(column, "")) for column in (
                    "taskCode", "summarySubject", "status", "startTime", "dueTime",
                )
            ],
        )


@app.command("upload-resource")
def upload_personal_todo_resource(
    app_id: str = typer.Argument(help="Application ID"),
    file_name: str = typer.Argument(help="File name, including extension"),
    content_type: str = typer.Argument(help="MIME content type"),
    org_id: str = typer.Argument(help="Organization ID"),
    file: str = typer.Option(..., "--file", help="Local file path to upload"),
    thumb: bool = typer.Option(False, "--thumb", help="Generate a thumbnail"),
    extension_info: str = typer.Option("", "--extension-info", help="Extension information"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Upload a resource and return its resource ID."""
    path = Path(file)
    if not path.is_file():
        raise typer.BadParameter(f"file does not exist: {file}")
    raw = path.read_bytes()
    result = get_client().upload_personal_todo_resource(
        app_id=app_id,
        size=len(raw),
        file_name=file_name,
        content_type=content_type,
        file_data=base64.b64encode(raw).decode("ascii"),
        org_id=org_id,
        extension_info=extension_info,
        thumb=thumb,
        user_token=user_token,
    )
    output_result(
        result,
        fields=["resource_id", "file_name", "size", "mime_type", "download_url"],
        title="Personal Todo Resource",
    )


@app.command("download-url")
def fetch_personal_todo_resource_download_url(
    resource_id: str = typer.Argument(help="Resource ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    file_name: str = typer.Option("", "--file-name", help="Optional base64-encoded file name"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a resource download URL."""
    result = get_client().fetch_personal_todo_resource_download_url(
        resource_id=resource_id,
        org_id=org_id,
        file_name=file_name,
        user_token=user_token,
    )
    output_result(result, fields=["url"], title="Resource Download URL")


@app.command("upload-url")
def fetch_personal_todo_resource_upload_url(
    file_name: str = typer.Argument(help="File name, including extension"),
    md5: str = typer.Argument(help="File MD5"),
    size: int = typer.Argument(help="File size in bytes"),
    org_id: str = typer.Argument(help="Organization ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a presigned upload URL for direct S3 upload."""
    result = get_client().fetch_personal_todo_resource_upload_url(
        file_name=file_name,
        md5=md5,
        size=size,
        org_id=org_id,
        user_token=user_token,
    )
    output_result(result, fields=["url"], title="Resource Upload URL")
