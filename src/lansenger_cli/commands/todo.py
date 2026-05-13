import typer
import json
from typing import Optional, List

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Manage todo tasks")


@app.command("create")
def create_todo_task(
    title: str = typer.Argument(help="Task title"),
    link: str = typer.Argument(help="Task link URL"),
    pc_link: str = typer.Argument(help="PC link URL"),
    executor_ids: str = typer.Argument(help="Executor IDs as comma-separated list"),
    org_id: str = typer.Argument(help="Organization ID"),
    type: int = typer.Option(1, "--type", "-t", help="1=notification, 2=approval"),
    source_id: str = typer.Option("", "--source-id", help="Source ID"),
    desc: str = typer.Option("", "--desc", "-d", help="Task description"),
    sender_id: str = typer.Option("", "--sender-id", help="Sender staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    ids = executor_ids.split(",")
    result = client.create_todo_task(
        title=title, link=link, pc_link=pc_link,
        executor_ids=ids, org_id=org_id, type=type,
        source_id=source_id, desc=desc,
        sender_id=sender_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Create Todo Result")


@app.command("update")
def update_todo_task(
    todotask_id: str = typer.Argument(help="Todo task ID"),
    title: str = typer.Argument(help="New title"),
    link: str = typer.Argument(help="New link URL"),
    pc_link: str = typer.Argument(help="New PC link URL"),
    org_id: str = typer.Argument(help="Organization ID"),
    desc: str = typer.Option("", "--desc", "-d", help="New description"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.update_todo_task(
        todotask_id=todotask_id, title=title, link=link,
        pc_link=pc_link, org_id=org_id, desc=desc,
        user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Update Todo Result")


@app.command("update-status")
def update_todo_task_status(
    todotask_id: str = typer.Argument(help="Todo task ID"),
    status: str = typer.Argument(help="Status: 11=pending read, 12=read, 21=pending do, 22=done"),
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.update_todo_task_status(
        todotask_id=todotask_id, status=status, org_id=org_id,
        staff_id=staff_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Update Todo Status Result")


@app.command("delete")
def delete_todo_task(
    todotask_id: str = typer.Argument(help="Todo task ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.delete_todo_task(
        todotask_id=todotask_id, org_id=org_id,
        staff_id=staff_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Delete Todo Result")


@app.command("list")
def fetch_todo_task_list(
    org_id: str = typer.Argument(help="Organization ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    app_ids: Optional[str] = typer.Option(None, "--app-ids", help="App IDs (comma-separated)"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    status_list: Optional[str] = typer.Option(None, "--status", help="Status list (comma-separated)"),
):
    client = get_client()
    app_ids_list = app_ids.split(",") if app_ids else None
    status_list_parsed = status_list.split(",") if status_list else None
    result = client.fetch_todo_task_list(
        org_id=org_id, user_token=user_token,
        app_ids=app_ids_list, staff_id=staff_id,
        status_list=status_list_parsed,
    )
    output_result(result, fields=["total"], title="Todo Task List")


@app.command("fetch-by-source")
def fetch_todo_task_by_source_id(
    source_id: str = typer.Argument(help="Source ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_todo_task_by_source_id(
        source_id=source_id, org_id=org_id,
        staff_id=staff_id, user_token=user_token,
    )
    output_result(result, fields=[
        "todotask_id", "source_id", "title", "desc",
        "status", "type", "link", "executor_ids",
    ], title="Todo Task")


@app.command("fetch-by-id")
def fetch_todo_task_by_id(
    todotask_id: str = typer.Argument(help="Todo task ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_todo_task_by_id(
        todotask_id=todotask_id, org_id=org_id,
        staff_id=staff_id, user_token=user_token,
    )
    output_result(result, fields=[
        "todotask_id", "source_id", "title", "desc",
        "status", "type", "link", "executor_ids",
    ], title="Todo Task")


@app.command("status-counts")
def fetch_todo_task_status_counts(
    staff_id: str = typer.Argument(help="Staff ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    app_id: str = typer.Option("", "--app-id", help="App ID"),
    status_list: Optional[str] = typer.Option(None, "--status", help="Status list (comma-separated)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    status_parsed = status_list.split(",") if status_list else None
    result = client.fetch_todo_task_status_counts(
        staff_id=staff_id, org_id=org_id,
        app_id=app_id, status_list=status_parsed,
        user_token=user_token,
    )
    output_result(result, fields=["status_counts"], title="Todo Status Counts")


@app.command("executor-status")
def update_executor_status(
    executor_status_list: str = typer.Argument(help="Executor status list as JSON: '[{\"executorId\":\"x\",\"status\":\"22\"}]'"),
    org_id: str = typer.Argument(help="Organization ID"),
    todotask_id: str = typer.Option("", "--task-id", help="Todo task ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    parsed = json.loads(executor_status_list)
    result = client.update_executor_status(
        executor_status_list=parsed, org_id=org_id,
        todotask_id=todotask_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Update Executor Status Result")


@app.command("add-executors")
def add_executors(
    executor_ids: str = typer.Argument(help="Executor IDs (comma-separated)"),
    org_id: str = typer.Argument(help="Organization ID"),
    todotask_id: str = typer.Option("", "--task-id", help="Todo task ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    ids = executor_ids.split(",")
    result = client.add_executors(
        executor_ids=ids, org_id=org_id,
        todotask_id=todotask_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Add Executors Result")


@app.command("delete-executors")
def delete_executors(
    executor_ids: str = typer.Argument(help="Executor IDs (comma-separated)"),
    org_id: str = typer.Argument(help="Organization ID"),
    todotask_id: str = typer.Option("", "--task-id", help="Todo task ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    ids = executor_ids.split(",")
    result = client.delete_executors(
        executor_ids=ids, org_id=org_id,
        todotask_id=todotask_id, user_token=user_token,
    )
    output_result(result, fields=["todotask_id"], title="Delete Executors Result")


@app.command("executor-list")
def fetch_executor_list(
    todotask_id: str = typer.Argument(help="Todo task ID"),
    org_id: str = typer.Argument(help="Organization ID"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    status_list: Optional[str] = typer.Option(None, "--status", help="Status list (comma-separated)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    status_parsed = status_list.split(",") if status_list else None
    result = client.fetch_executor_list(
        todotask_id=todotask_id, org_id=org_id,
        staff_id=staff_id, status_list=status_parsed,
        user_token=user_token,
    )
    output_result(result, fields=["total"], title="Executor List")