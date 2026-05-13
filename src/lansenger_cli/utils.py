from lansenger_sdk import LansengerSyncClient, CredentialStore, LansengerConfig
from rich import print as rprint
from rich.console import Console
from rich.table import Table

console = Console()
_json_output = False


def set_json_output(value: bool):
    global _json_output
    _json_output = value


def is_json_output() -> bool:
    return _json_output


def get_store() -> CredentialStore:
    return CredentialStore()


def get_client(store_path: str = "") -> LansengerSyncClient:
    store = CredentialStore(path=store_path) if store_path else CredentialStore()
    creds = store.load_credentials()
    if not creds.get("app_id") or not creds.get("app_secret"):
        env_config = LansengerConfig.from_env()
        if env_config.is_configured():
            return LansengerSyncClient.from_config(env_config)
        rprint("[red]Error:[/red] No credentials configured. Run [bold]lansenger config set[/bold] first, or set LANSENGER_APP_ID / LANSENGER_APP_SECRET env vars.")
        raise SystemExit(1)
    config = LansengerConfig(
        app_id=creds["app_id"],
        app_secret=creds["app_secret"],
        api_gateway_url=creds.get("api_gateway_url", "https://open.e.lanxin.cn/open/apigw"),
        passport_url=creds.get("passport_url", ""),
    )
    return LansengerSyncClient.from_config(config)


def output_result(result, fields: list[str] | None = None, title: str = ""):
    if is_json_output():
        rprint(result.to_dict())
        return
    if not result.success:
        rprint(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)
    if fields:
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Field")
        table.add_column("Value")
        for f in fields:
            val = getattr(result, f, None)
            if val is not None:
                if isinstance(val, (list, dict)):
                    val = str(val)
                table.add_row(f, str(val))
        console.print(table)
    else:
        rprint(result.to_dict())


def output_list(items: list, columns: list[str], title: str = "", row_mapper=None):
    if is_json_output():
        rprint([item.to_dict() if hasattr(item, "to_dict") else item for item in items])
        return
    if not items:
        rprint("[yellow]No results.[/yellow]")
        return
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for item in items:
        if row_mapper:
            row = row_mapper(item)
        else:
            row = [str(getattr(item, col, "")) for col in columns]
        table.add_row(*row)
    console.print(table)