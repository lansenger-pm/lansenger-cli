import typer
import json
from rich import print as rprint

from lansenger_cli.utils import is_json_output, console, get_active_profile

app = typer.Typer(help="Parse and verify callback events")


def _resolve_encoding_key(cli_value: str, profile: str = "") -> str:
    if cli_value:
        return cli_value
    from lansenger_sdk import CredentialStore
    p = profile or get_active_profile()
    store = CredentialStore(profile=p)
    creds = store.load_credentials()
    val = creds.get("encoding_key", "")
    if val:
        rprint(f"[dim]Using encoding_key from credential store (profile: {p})[/dim]")
    return val


def _resolve_callback_token(cli_value: str, encoding_key: str, profile: str = "") -> str:
    if cli_value:
        return cli_value
    from lansenger_sdk import CredentialStore
    p = profile or get_active_profile()
    store = CredentialStore(profile=p)
    creds = store.load_credentials()
    val = creds.get("callback_token", "")
    if val:
        rprint(f"[dim]Using callback_token from credential store (profile: {p})[/dim]")
    return val


@app.command("parse-payload")
def parse_callback_payload(
    encrypted_data: str = typer.Argument(help="Callback data (plain JSON or encrypted dataEncrypt value)"),
    encoding_key: str = typer.Option("", "--encoding-key", help="Base64-encoded AES key for decryption (reads from credential store if empty)"),
    callback_token: str = typer.Option("", "--callback-token", help="Token for signature verification (reads from credential store if empty; falls back to encoding_key)"),
    known_app_id: str = typer.Option("", "--known-app-id", help="Known appId to help split orgId/appId during decryption"),
    verify_signature: bool = typer.Option(False, "--verify-sig", help="Verify signature before parsing"),
    timestamp: str = typer.Option("", "--timestamp", help="Timestamp for signature verification"),
    nonce: str = typer.Option("", "--nonce", help="Nonce for signature verification"),
    signature: str = typer.Option("", "--signature", help="Signature to verify"),
    profile: str = typer.Option("", "--profile", "-P", help="Credential profile (overrides global --profile)"),
):
    """Parse callback payload (decrypt and verify)"""
    from lansenger_sdk import parse_callback_payload
    p = profile or get_active_profile()
    resolved_key = _resolve_encoding_key(encoding_key, p)
    resolved_token = _resolve_callback_token(callback_token, resolved_key, p)
    events = parse_callback_payload(
        encrypted_data,
        encoding_key=resolved_key,
        verify_signature=verify_signature,
        timestamp=timestamp,
        nonce=nonce,
        signature=signature,
        callback_token=resolved_token,
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
    encoding_key: str = typer.Option("", "--encoding-key", help="Base64-encoded AES key for decryption (reads from credential store if empty)"),
    known_app_id: str = typer.Option("", "--known-app-id", help="Known appId to help split orgId/appId in decrypted result"),
    profile: str = typer.Option("", "--profile", "-P", help="Credential profile (overrides global --profile)"),
):
    """Decrypt callback payload"""
    from lansenger_sdk import decrypt_callback_payload
    p = profile or get_active_profile()
    resolved_key = _resolve_encoding_key(encoding_key, p)
    if not resolved_key:
        rprint("[red]Error:[/red] encoding_key is required for decryption. Pass --encoding-key or set it via [bold]lansenger config set encoding_key[/bold].")
        raise typer.Exit(1)
    result = decrypt_callback_payload(encrypted_data, resolved_key, known_app_id=known_app_id)
    if is_json_output():
        rprint(json.dumps(result, indent=2, ensure_ascii=False))
        return
    rprint(f"[bold]orgId:[/bold] {result.get('orgId', '')}")
    rprint(f"[bold]appId:[/bold] {result.get('appId', '')}")
    rprint(f"[bold]events length:[/bold] {result.get('length', 0)}")
    rprint("[bold]events:[/bold]")
    rprint(json.dumps(result.get("events", []), indent=2, ensure_ascii=False))


@app.command("verify-signature")
def verify_callback_signature(
    timestamp: str = typer.Argument(help="Timestamp"),
    nonce: str = typer.Argument(help="Nonce"),
    signature: str = typer.Argument(help="Signature"),
    encoding_key: str = typer.Option("", "--encoding-key", help="Encoding key, used as token if callback-token not provided (reads from credential store if empty)"),
    data_encrypt: str = typer.Option("", "--data-encrypt", help="The encrypted dataEncrypt value (required for correct signature verification)"),
    callback_token: str = typer.Option("", "--callback-token", help="Token from developer center callback config (reads from credential store if empty; falls back to encoding_key)"),
    profile: str = typer.Option("", "--profile", "-P", help="Credential profile (overrides global --profile)"),
):
    """Verify callback signature"""
    from lansenger_sdk import verify_callback_signature as _verify
    p = profile or get_active_profile()
    resolved_key = _resolve_encoding_key(encoding_key, p)
    if not resolved_key:
        rprint("[red]Error:[/red] encoding_key is required for signature verification. Pass --encoding-key or set it via [bold]lansenger config set encoding_key[/bold].")
        raise typer.Exit(1)
    resolved_token = _resolve_callback_token(callback_token, resolved_key, p)
    valid = _verify(timestamp, nonce, signature, resolved_key, data_encrypt=data_encrypt, callback_token=resolved_token)
    if is_json_output():
        rprint(json.dumps({"valid": valid}, ensure_ascii=False))
        return
    rprint(f"Signature valid: {valid}")


@app.command("event-types")
def get_callback_event_types():
    """Get callback event types"""
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
