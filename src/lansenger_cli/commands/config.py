import typer
from rich import print as rprint

from lansenger_sdk import CredentialStore

from lansenger_cli.utils import get_store, get_active_profile, output_result, is_json_output

app = typer.Typer(help="Manage CLI configuration (credentials, tokens)")

VALID_KEYS = ["app_id", "app_secret", "api_gateway_url", "passport_url", "redirect_uri", "encoding_key", "callback_token"]

_SENSITIVE_KEYS = {"app_secret", "encoding_key", "callback_token"}


def _mask_sensitive(data: dict) -> None:
    """Mask sensitive fields in-place for JSON output."""
    profiles = data.get("profiles", {})
    for profile_data in profiles.values():
        if isinstance(profile_data, dict):
            for key in _SENSITIVE_KEYS:
                if key in profile_data and profile_data[key]:
                    profile_data[key] = "***"


@app.command("set")
def config_set(
    key: str = typer.Argument(help=f"Config key: {', '.join(VALID_KEYS)}"),
    value: str = typer.Argument(help="Config value"),
    profile: str = typer.Option("", "--profile", "-P", help="Profile name (overrides global --profile)"),
):
    """Set configuration value"""
    p = profile or get_active_profile()
    if key not in VALID_KEYS:
        rprint(f"[red]Error:[/red] Invalid key '{key}'. Valid keys: {', '.join(VALID_KEYS)}")
        raise typer.Exit(1)
    store = CredentialStore(profile=p)
    creds = store.load_credentials()
    creds[key] = value
    store.save_credentials(
        app_id=creds.get("app_id", ""),
        app_secret=creds.get("app_secret", ""),
        api_gateway_url=creds.get("api_gateway_url", ""),
        passport_url=creds.get("passport_url", ""),
        redirect_uri=creds.get("redirect_uri", ""),
        encoding_key=creds.get("encoding_key", ""),
        callback_token=creds.get("callback_token", ""),
    )
    rprint(f"[green]Set[/green] {key} = {value} [dim](profile: {p})[/dim]")


@app.command("show")
def config_show(
    profile: str = typer.Option("", "--profile", "-P", help="Profile name (overrides global --profile)"),
):
    """Show current configuration"""
    p = profile or get_active_profile()
    store = CredentialStore(profile=p)
    if is_json_output():
        data = store.load()
        _mask_sensitive(data)
        rprint(data)
        return
    creds = store.load_credentials()
    has = store.has_credentials()
    full = store.has_full_config()
    rprint(f"Profile: {p}")
    rprint(f"Credentials configured: {has}")
    rprint(f"Full config available: {full}")
    rprint(f"Store path: {store.path}")
    for k, v in creds.items():
        display = v if k in ("api_gateway_url", "passport_url") else ("***" if v else "(empty)")
        rprint(f"  {k}: {display}")


@app.command("clear")
def config_clear(
    profile: str = typer.Option("", "--profile", "-P", help="Profile name (overrides global --profile)"),
    all_profiles: bool = typer.Option(False, "--all", help="Delete entire state file"),
):
    """Clear configuration"""
    if all_profiles:
        store = CredentialStore()
        store.clear()
        rprint("[green]Cleared[/green] entire state file (all profiles).")
        return
    p = profile or get_active_profile()
    store = CredentialStore(profile=p)
    store.clear_profile()
    rprint(f"[green]Cleared[/green] profile '{p}'.")


@app.command("list-profiles")
def config_list_profiles():
    """List all configuration profiles"""
    store = CredentialStore()
    profiles = store.list_profiles()
    active = store.get_active_profile()
    if not profiles:
        rprint("[yellow]No profiles configured.[/yellow]")
        return
    if is_json_output():
        rprint({"profiles": profiles, "active": active})
        return
    rprint(f"Active profile: [bold]{active}[/bold]")
    for p in profiles:
        marker = " ← active" if p == active else ""
        p_store = CredentialStore(profile=p)
        p_creds = p_store.load_credentials()
        has = p_store.has_credentials()
        rprint(f"  {p}{marker}  {'[green]✓[/green]' if has else '[red]✗[/red]'}  app_id={p_creds.get('app_id', '(empty)')}  gateway={p_creds.get('api_gateway_url', '(empty)')}")


@app.command("delete-profile")
def config_delete_profile(
    profile: str = typer.Argument(help="Profile name to delete"),
):
    """Delete a profile and all its credentials"""
    store = CredentialStore()
    was_active = store.get_active_profile() == profile
    if not store.delete_profile_by_name(profile):
        rprint(f"[red]Error:[/red] Profile '{profile}' does not exist.")
        raise typer.Exit(1)
    if is_json_output():
        rprint({"deleted": profile, "active": store.get_active_profile()})
        return
    rprint(f"[green]Deleted[/green] profile '{profile}'.")
    if was_active:
        rprint(f"[dim]Active profile switched to 'default'.[/dim]")