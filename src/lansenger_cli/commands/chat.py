import typer

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Chat list and message history (4.24 MCP)")


@app.command("list")
def fetch_chat_list(
    chat_type: int = typer.Option(0, "--type", "-t", help="0=all, 1=private, 2=group"),
    keyword: str = typer.Option("", "--keyword", "-k", help="Search keyword (only for type 1 or 2)"),
    start_time: int = typer.Option(0, "--start", help="Start time in microseconds"),
    end_time: int = typer.Option(0, "--end", help="End time in microseconds"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_chat_list(
        chat_type=chat_type, keyword=keyword,
        start_time=start_time, end_time=end_time,
        user_token=user_token,
    )
    if result.success:
        output_result(result, fields=[], title="Chat List")
        if result.staff_infos:
            output_list(result.staff_infos, columns=["Staff ID", "Name", "Sectors"], row_mapper=lambda s: [
                getattr(s, "staff_id", ""), getattr(s, "staff_name", ""),
                str(getattr(s, "sector_names", "")),
            ])
        if result.group_infos:
            output_list(result.group_infos, columns=["Group ID", "Name"], row_mapper=lambda g: [
                getattr(g, "group_id", ""), getattr(g, "group_name", ""),
            ])
    else:
        output_result(result)


@app.command("messages")
def fetch_chat_messages(
    staff_id: str = typer.Option("", "--staff-id", help="Private chat partner staffId"),
    group_id: str = typer.Option("", "--group-id", help="Group openId"),
    page_size: int = typer.Option(100, "--size", "-s", help="Per-page count (max 100)"),
    base_version: str = typer.Option("0", "--version", help="Deep pagination cursor, first call: 0"),
    start_time: int = typer.Option(0, "--start", help="Start time in microseconds"),
    end_time: int = typer.Option(0, "--end", help="End time in microseconds"),
    sender_id: str = typer.Option("", "--sender-id", help="Filter by sender staffId"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    client = get_client()
    result = client.fetch_chat_messages(
        staff_id=staff_id, group_id=group_id,
        page_size=page_size, base_version=base_version,
        start_time=start_time, end_time=end_time,
        sender_id=sender_id, user_token=user_token,
    )
    if result.success:
        output_result(result, fields=["has_more", "total", "last_version", "name", "chat_type"], title="Chat Messages")
        if result.messages:
            output_list(result.messages, columns=["Time", "Sender", "Type"], row_mapper=lambda m: [
                getattr(m, "send_time", ""), getattr(m, "sender", ""),
                getattr(m, "message_type", ""),
            ])
    else:
        output_result(result)