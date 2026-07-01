import typer

from lansenger_cli.utils import get_client, output_result

app = typer.Typer(help="Manage bot slash commands (4.37)")


@app.command("create")
def create_bot_commands(
    scope_type: int = typer.Argument(help="Scope: 1=single group single member, 2=single group admin, 3=single chat, 4=all group admins, 5=all groups, 6=all private chats, 7=global"),
    commands: str = typer.Argument(help="Commands as JSON array: '[{\"command\":\"/add\",\"description\":\"desc\",\"icon\":\"xxx\"}]'"),
    chat_id: str = typer.Option("", "--chat-id", help="Group/staff openId (for scope 1/2/3)"),
    chat_type: str = typer.Option("", "--chat-type", help="group or staff (for scope 1/2/3)"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff openId (for scope 1)"),
):
    """Create bot commands"""
    import json
    commands_list = json.loads(commands)
    client = get_client()
    result = client.create_bot_commands(
        scope_type=scope_type,
        commands=commands_list,
        chat_id=chat_id,
        chat_type=chat_type,
        staff_id=staff_id,
    )
    output_result(result, title="Create Bot Commands Result")


@app.command("query")
def fetch_bot_commands(
    scope_type: int = typer.Argument(help="Scope (1-7) to query"),
    chat_id: str = typer.Option("", "--chat-id", help="Group/staff openId (for scope 1/2/3)"),
    chat_type: str = typer.Option("", "--chat-type", help="group or staff (for scope 1/2/3)"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff openId (for scope 1)"),
):
    """Query bot commands"""
    client = get_client()
    result = client.fetch_bot_commands(
        scope_type=scope_type,
        chat_id=chat_id,
        chat_type=chat_type,
        staff_id=staff_id,
    )
    output_result(result, fields=["scope_type", "chat_id", "chat_type", "staff_id"], title="Bot Commands")
    if result.success and result.commands:
        from lansenger_cli.utils import output_list
        output_list(result.commands, columns=["Command", "Description", "Icon"], row_mapper=lambda c: [
            c.get("command", ""), c.get("description", ""), c.get("icon", ""),
        ])


@app.command("delete")
def delete_bot_commands(
    scope_type: int = typer.Argument(help="Scope (1-7) to delete commands for"),
    chat_id: str = typer.Option("", "--chat-id", help="Group/staff openId (for scope 1/2/3)"),
    chat_type: str = typer.Option("", "--chat-type", help="group or staff (for scope 1/2/3)"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff openId (for scope 1)"),
):
    """Delete bot commands"""
    client = get_client()
    result = client.delete_bot_commands(
        scope_type=scope_type,
        chat_id=chat_id,
        chat_type=chat_type,
        staff_id=staff_id,
    )
    output_result(result, title="Delete Bot Commands Result")
