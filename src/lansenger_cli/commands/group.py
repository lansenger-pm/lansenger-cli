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
    staff_id_list: Optional[List[str]] = typer.Option(None, "--staff", "-S", help="Staff IDs to add"),
    department_id_list: Optional[List[str]] = typer.Option(None, "--dept", "-D", help="Department IDs to add"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Create a new group"""
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
    """Fetch group information"""
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
    """Fetch group members"""
    client = get_client()
    result = client.fetch_group_members(
        group_id=group_id, user_token=user_token,
        page_offset=page_offset, page_size=page_size,
    )
    if result.success:
        output_result(result, fields=["total_members"], title="Group Members")
        if result.members:
            output_list(result.members, columns=["Staff ID", "Name", "Role"], row_mapper=lambda m: [
                m.get("staffId", ""), m.get("name", ""), m.get("role", "")
            ])
    else:
        output_result(result)


@app.command("list")
def fetch_group_list(
    user_token: str = typer.Option("", "--user-token", help="User token"),
    page_offset: int = typer.Option(0, "--page", "-p", help="Page offset"),
    page_size: int = typer.Option(100, "--size", "-s", help="Page size"),
):
    """Fetch user's group list"""
    client = get_client()
    result = client.fetch_group_list(user_token=user_token, page_offset=page_offset, page_size=page_size)
    output_result(result, fields=["total_group_ids"], title="Group List")


@app.command("check")
def check_is_in_group(
    group_id: str = typer.Argument(help="Group ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID to check"),
):
    """Check if a staff member is in a group"""
    client = get_client()
    result = client.check_is_in_group(group_id=group_id, user_token=user_token, staff_id=staff_id)
    output_result(result, fields=["is_in_group"], title="Is In Group")


@app.command("update")
def update_group_info(
    group_id: str = typer.Argument(help="Group ID"),
    name: str = typer.Option("", "--name", help="New group name"),
    description: str = typer.Option("", "--desc", help="New description"),
    owner_id: str = typer.Option("", "--owner", help="New owner ID"),
    avatar_id: str = typer.Option("", "--avatar", help="New avatar ID"),
    assistant: Optional[List[str]] = typer.Option(None, "--assistant", help="Staff IDs to promote to assistant"),
    demote_assistant: Optional[List[str]] = typer.Option(None, "--demote-assistant", help="Staff IDs to demote from assistant"),
    manage_mode: Optional[int] = typer.Option(None, "--manage-mode", help="0=all manage, 1=owner only"),
    location_share: Optional[bool] = typer.Option(None, "--location-share", help="Enable/disable location sharing"),
    needs_confirm: Optional[bool] = typer.Option(None, "--needs-confirm", help="Join requires confirmation"),
    is_public: Optional[bool] = typer.Option(None, "--is-public", help="Public visibility"),
    max_members: Optional[int] = typer.Option(None, "--max-members", help="Maximum member count"),
    max_history_msg_count: Optional[int] = typer.Option(None, "--max-history", help="Max history message count"),
    remind_all: Optional[bool] = typer.Option(None, "--remind-all", help="@mention enabled/disabled"),
    send_msg_status: Optional[bool] = typer.Option(None, "--mute", help="Group mute on/off"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Update group information"""
    client = get_client()
    result = client.update_group_info(
        group_id=group_id, name=name, description=description,
        owner_id=owner_id, avatar_id=avatar_id,
        assistant=assistant, demote_assistant=demote_assistant,
        manage_mode=manage_mode, location_share=location_share,
        needs_confirm=needs_confirm, is_public=is_public,
        max_members=max_members, max_history_msg_count=max_history_msg_count,
        remind_all=remind_all, send_msg_status=send_msg_status,
        user_token=user_token,
    )
    output_result(result, title="Update Group Result")


@app.command("update-members")
def update_group_members(
    group_id: str = typer.Argument(help="Group ID"),
    add_user: Optional[List[str]] = typer.Option(None, "--add", "-A", help="Staff IDs to add"),
    del_user: Optional[List[str]] = typer.Option(None, "--remove", "-X", help="Staff IDs to remove"),
    add_dept: Optional[List[str]] = typer.Option(None, "--add-dept", "-D", help="Department IDs to add"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Add/remove group members"""
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
    """Dismiss/delete a group"""
    client = get_client()
    result = client.dismiss_group(group_id=group_id, user_token=user_token)
    output_result(result, title="Dismiss Group Result")