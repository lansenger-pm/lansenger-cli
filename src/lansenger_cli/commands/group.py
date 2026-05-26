import typer
from typing import Optional, List

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Manage groups")


@app.command("create")
def create_group(
    name: str = typer.Argument(help="Group name"),
    org_id: str = typer.Argument(help="Organization ID"),
    owner_id: str = typer.Option("", "--owner", help="Owner staff ID"),
    description: str = typer.Option("", "--desc", "-d", help="Group description"),
    avatar_id: str = typer.Option("", "--avatar", help="Avatar ID"),
    staff_id_list: Optional[List[str]] = typer.Option(None, "--staff", help="Staff IDs to add"),
    department_id_list: Optional[List[str]] = typer.Option(None, "--dept", help="Department IDs to add"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.create_group(
        name=name, org_id=org_id, owner_id=owner_id,
        description=description, avatar_id=avatar_id,
        staff_id_list=staff_id_list, department_id_list=department_id_list,
        user_token=user_token,
    )
    output_result(result, fields=["group_id", "total_members"], title="Create Group Result")


@app.command("info")
def fetch_group_info(
    group_id: str = typer.Argument(help="Group ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_group_info(group_id=group_id, user_token=user_token)
    output_result(result, fields=[
        "name", "description", "owner", "creator", "state",
        "manage_mode", "is_public", "max_members", "total_members",
    ], title="Group Info")


@app.command("members")
def fetch_group_members(
    group_id: str = typer.Argument(help="Group ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    page_offset: int = typer.Option(0, "--page", "-p", help="Page offset"),
    page_size: int = typer.Option(100, "--size", "-s", help="Page size"),
):
    client = get_client()
    result = client.fetch_group_members(
        group_id=group_id, user_token=user_token,
        page_offset=page_offset, page_size=page_size,
    )
    if result.success:
        output_result(result, fields=["total_members"], title="Group Members")
        if result.members:
            output_list(result.members, columns=["Staff ID", "Name", "Role"], row_mapper=lambda m: [
                getattr(m, "staff_id", ""), getattr(m, "name", ""), getattr(m, "role", "")
            ])
    else:
        output_result(result)


@app.command("list")
def fetch_group_list(
    user_token: str = typer.Option("", "--user-token", help="User token"),
    page_offset: int = typer.Option(0, "--page", "-p", help="Page offset"),
    page_size: int = typer.Option(100, "--size", "-s", help="Page size"),
):
    client = get_client()
    result = client.fetch_group_list(user_token=user_token, page_offset=page_offset, page_size=page_size)
    output_result(result, fields=["total_group_ids"], title="Group List")


@app.command("check")
def check_is_in_group(
    group_id: str = typer.Argument(help="Group ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID to check"),
):
    client = get_client()
    result = client.check_is_in_group(group_id=group_id, user_token=user_token, staff_id=staff_id)
    output_result(result, fields=["is_in_group"], title="Is In Group")


@app.command("update")
def update_group_info(
    group_id: str = typer.Argument(help="Group ID"),
    name: str = typer.Option("", "--name", help="New group name"),
    description: str = typer.Option("", "--desc", help="New description"),
    owner_id: str = typer.Option("", "--owner", help="New owner ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.update_group_info(
        group_id=group_id, name=name, description=description,
        owner_id=owner_id, user_token=user_token,
    )
    output_result(result, title="Update Group Result")


@app.command("update-members")
def update_group_members(
    group_id: str = typer.Argument(help="Group ID"),
    add_user: Optional[List[str]] = typer.Option(None, "--add", help="Staff IDs to add"),
    del_user: Optional[List[str]] = typer.Option(None, "--remove", help="Staff IDs to remove"),
    add_dept: Optional[List[str]] = typer.Option(None, "--add-dept", help="Department IDs to add"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.update_group_members(
        group_id=group_id, add_user_list=add_user,
        del_user_list=del_user, add_department_id_list=add_dept,
        user_token=user_token,
    )
    output_result(result, fields=["total_members", "added_staff_count", "deleted_staff_count"], title="Update Members Result")


@app.command("dismiss")
def dismiss_group(
    group_id: str = typer.Argument(help="Group ID to dismiss/delete"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.dismiss_group(group_id=group_id, user_token=user_token)
    output_result(result, title="Dismiss Group Result")