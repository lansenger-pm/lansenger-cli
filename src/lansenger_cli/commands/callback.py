import typer
import json
from rich import print as rprint

from lansenger_cli.utils import is_json_output, console

app = typer.Typer(help="Parse and verify callback events")


@app.command("parse-payload")
def parse_callback_payload(
    encrypted_data: str = typer.Argument(help="Encrypted callback data"),
    encoding_key: str = typer.Option("", "--encoding-key", help="Encoding key for decryption"),
    verify_signature: bool = typer.Option(False, "--verify-sig", help="Verify signature"),
    timestamp: str = typer.Option("", "--timestamp", help="Timestamp for signature verification"),
    nonce: str = typer.Option("", "--nonce", help="Nonce for signature verification"),
    signature: str = typer.Option("", "--signature", help="Signature to verify"),
):
    from lansenger_sdk import parse_callback_payload
    events = parse_callback_payload(
        encrypted_data,
        encoding_key=encoding_key,
        verify_signature=verify_signature,
        timestamp=timestamp,
        nonce=nonce,
        signature=signature,
    )
    if is_json_output():
        rprint(json.dumps([e.to_dict() if hasattr(e, "to_dict") else str(e) for e in events], indent=2, ensure_ascii=False))
        return
    for event in events:
        rprint(f"[bold cyan]Event #{event.event_id}[/bold cyan] — {event.event_type} ({event.category})")
        if hasattr(event, "data") and hasattr(event.data, "to_dict"):
            rprint(json.dumps(event.data.to_dict(), indent=2, ensure_ascii=False))
        else:
            rprint(event.data)


@app.command("verify-signature")
def verify_callback_signature(
    timestamp: str = typer.Argument(help="Timestamp"),
    nonce: str = typer.Argument(help="Nonce"),
    signature: str = typer.Argument(help="Signature"),
    encoding_key: str = typer.Argument(help="Encoding key"),
):
    from lansenger_sdk import verify_callback_signature
    valid = verify_callback_signature(timestamp, nonce, signature, encoding_key)
    rprint(f"Signature valid: {valid}")


@app.command("event-types")
def get_callback_event_types():
    from lansenger_sdk import get_callback_event_types
    types = get_callback_event_types()
    if is_json_output():
        rprint(json.dumps(types, indent=2, ensure_ascii=False))
        return
    from rich.table import Table
    table = Table(title="Callback Event Types", show_header=True, header_style="bold cyan")
    table.add_column("Event Type")
    table.add_column("Category")
    for event_type, category in types.items():
        table.add_row(event_type, category)
    console.print(table)