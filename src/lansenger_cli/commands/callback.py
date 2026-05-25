import typer
import json
from rich import print as rprint

from lansenger_cli.utils import is_json_output, console

app = typer.Typer(help="Parse and verify callback events")


@app.command("parse-payload")
def parse_callback_payload(
    encrypted_data: str = typer.Argument(help="Callback data (plain JSON or encrypted dataEncrypt value)"),
    encoding_key: str = typer.Option("", "--encoding-key", help="Base64-encoded AES key for decryption"),
    callback_token: str = typer.Option("", "--callback-token", help="Token for signature verification (from developer center callback config; falls back to encoding_key)"),
    known_app_id: str = typer.Option("", "--known-app-id", help="Known appId to help split orgId/appId during decryption"),
    verify_signature: bool = typer.Option(False, "--verify-sig", help="Verify signature before parsing"),
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
        callback_token=callback_token,
        known_app_id=known_app_id,
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


@app.command("decrypt-payload")
def decrypt_callback_payload(
    encrypted_data: str = typer.Argument(help="Encrypted dataEncrypt value"),
    encoding_key: str = typer.Option(..., "--encoding-key", help="Base64-encoded AES key for decryption"),
    known_app_id: str = typer.Option("", "--known-app-id", help="Known appId to help split orgId/appId in decrypted result"),
):
    from lansenger_sdk import decrypt_callback_payload
    result = decrypt_callback_payload(encrypted_data, encoding_key, known_app_id=known_app_id)
    if is_json_output():
        rprint(json.dumps(result, indent=2, ensure_ascii=False))
        return
    rprint(f"[bold]orgId:[/bold] {result.get('orgId', '')}")
    rprint(f"[bold]appId:[/bold] {result.get('appId', '')}")
    rprint(f"[bold]events length:[/bold] {result.get('length', 0)}")
    rprint(f"[bold]events:[/bold]")
    rprint(json.dumps(result.get("events", []), indent=2, ensure_ascii=False))


@app.command("verify-signature")
def verify_callback_signature(
    timestamp: str = typer.Argument(help="Timestamp"),
    nonce: str = typer.Argument(help="Nonce"),
    signature: str = typer.Argument(help="Signature"),
    encoding_key: str = typer.Argument(help="Encoding key (used as token if callback-token not provided)"),
    data_encrypt: str = typer.Option("", "--data-encrypt", help="The encrypted dataEncrypt value (required for correct signature verification)"),
    callback_token: str = typer.Option("", "--callback-token", help="Token from developer center callback config (falls back to encoding_key)"),
):
    from lansenger_sdk import verify_callback_signature as _verify
    valid = _verify(timestamp, nonce, signature, encoding_key, data_encrypt=data_encrypt, callback_token=callback_token)
    if is_json_output():
        rprint(json.dumps({"valid": valid}, ensure_ascii=False))
        return
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