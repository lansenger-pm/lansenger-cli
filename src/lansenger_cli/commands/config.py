import typer
from rich import print as rprint

from lansenger_sdk import CredentialStore

from lansenger_cli.utils import get_store, output_result, is_json_output

app = typer.Typer(help="Manage CLI configuration (credentials, tokens)")

VALID_KEYS = ["app_id", "app_secret", "api_gateway_url", "passport_url"]


@app.command("set")
def config_set(
    key: str = typer.Argument(help=f"Config key: {', '.join(VALID_KEYS)}"),
    value: str = typer.Argument(help="Config value"),
):
    if key not in VALID_KEYS:
        rprint(f"[red]Error:[/red] Invalid key '{key}'. Valid keys: {', '.join(VALID_KEYS)}")
        raise typer.Exit(1)
    store = get_store()
    creds = store.load_credentials()
    creds[key] = value
    store.save_credentials(
        app_id=creds.get("app_id", ""),
        app_secret=creds.get("app_secret", ""),
        api_gateway_url=creds.get("api_gateway_url", ""),
        passport_url=creds.get("passport_url", ""),
    )
    rprint(f"[green]Set[/green] {key} = {value}")


@app.command("show")
def config_show():
    store = get_store()
    if is_json_output():
        rprint(store.load())
        return
    creds = store.load_credentials()
    has = store.has_credentials()
    full = store.has_full_config()
    rprint(f"Credentials configured: {has}")
    rprint(f"Full config available: {full}")
    rprint(f"Store path: {store.path}")
    for k, v in creds.items():
        display = v if k in ("api_gateway_url", "passport_url") else ("***" if v else "(empty)")
        rprint(f"  {k}: {display}")


@app.command("clear")
def config_clear():
    store = get_store()
    store.clear()
    rprint("[green]Cleared[/green] all stored configuration.")