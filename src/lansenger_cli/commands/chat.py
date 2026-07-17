import typer
import time
import json
from rich import print as rprint

from lansenger_cli.utils import get_client, output_result, output_list, is_json_output, _result_to_dict

app = typer.Typer(help="Chat list and message history (4.24 MCP)")


@app.command("list")
def fetch_chat_list(
    chat_type: int = typer.Option(0, "--type", "-t", help="0=all, 1=private, 2=group"),
    keyword: str = typer.Option("", "--keyword", "-k", help="Search keyword (only for type 1 or 2)"),
    start_time: int = typer.Option(0, "--start", help="Start time in microseconds"),
    end_time: int = typer.Option(0, "--end", help="End time in microseconds"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch chat list"""
    client = get_client()
    result = client.fetch_chat_list(
        chat_type=chat_type, keyword=keyword,
        start_time=start_time, end_time=end_time,
        user_token=user_token,
    )
    if is_json_output():
        import json
        print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))
        return
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
    split_month: bool = typer.Option(False, "--split-month", help="Auto-split query by month when range > 1 month"),
    progress: bool = typer.Option(False, "--progress", help="Show pagination progress (pages/messages fetched)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch chat message history"""
    client = get_client()
    if not staff_id and not group_id:
        rprint("[red]Error:[/red] At least one of --staff-id or --group-id is required.")
        raise typer.Exit(1)
    if not split_month:
        result = client.fetch_chat_messages(
            staff_id=staff_id, group_id=group_id,
            page_size=page_size, base_version=base_version,
            start_time=start_time, end_time=end_time,
            sender_id=sender_id, user_token=user_token,
        )
        if is_json_output():
            print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))
            return
        if result.success:
            output_result(result, fields=["has_more", "total", "last_version", "name", "chat_type"], title="Chat Messages")
            if result.messages:
                output_list(result.messages, columns=["Time", "Sender", "Type"], row_mapper=lambda m: [
                    getattr(m, "send_time", ""), getattr(m, "sender", ""),
                    getattr(m, "message_type", ""),
                ])
        else:
            output_result(result)
        return

    all_messages = []
    page_count = 0
    msg_count = 0

    start_ms = start_time if start_time else 0
    end_ms = end_time if end_time else int(time.time() * 1_000_000)

    months = _split_months(start_ms, end_ms)
    for i, (ms_start, ms_end) in enumerate(months):
        cursor = "0"
        while True:
            result = client.fetch_chat_messages(
                staff_id=staff_id, group_id=group_id,
                page_size=page_size, base_version=cursor,
                start_time=ms_start, end_time=ms_end,
                sender_id=sender_id, user_token=user_token,
            )
            if not result.success:
                output_result(result)
                return
            page_count += 1
            msg_count += len(result.messages) if result.messages else 0
            all_messages.extend(result.messages or [])

            if progress and not is_json_output():
                rprint(f"[dim]Month {i+1}/{len(months)} | Page {page_count} | {msg_count} messages total[/dim]")

            if not (result.messages and getattr(result, "has_more", False)):
                break
            cursor = str(getattr(result, "last_version", ""))

    if is_json_output():
        print(json.dumps([m.to_dict() if hasattr(m, "to_dict") else str(m) for m in all_messages], indent=2, ensure_ascii=False))
        return
    if progress:
        rprint(f"[bold]Done:[/bold] {page_count} pages, {msg_count} messages across {len(months)} months")
    if all_messages:
        output_list(all_messages, columns=["Time", "Sender", "Type"], row_mapper=lambda m: [
            getattr(m, "send_time", ""), getattr(m, "sender", ""),
            getattr(m, "message_type", ""),
        ])


def _split_months(start_us: int, end_us: int) -> list[tuple[int, int]]:
    import calendar as cal_mod
    from datetime import datetime

    results = []
    start_dt = datetime.fromtimestamp(start_us / 1_000_000) if start_us else datetime(2020, 1, 1)
    end_dt = datetime.fromtimestamp(end_us / 1_000_000)

    year, month = start_dt.year, start_dt.month
    while (year, month) <= (end_dt.year, end_dt.month):
        last_day = cal_mod.monthrange(year, month)[1]
        ms_start = int(datetime(year, month, 1).timestamp() * 1_000_000)
        ms_end = int(datetime(year, month, last_day, 23, 59, 59).timestamp() * 1_000_000)
        results.append((ms_start, ms_end))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return results
