import os
import dataclasses

from lansenger_sdk import LansengerSyncClient, CredentialStore, LansengerConfig
from rich import print as rprint
from rich.console import Console
from rich.table import Table

console = Console()
_json_output = False
_active_profile = "default"


def set_json_output(value: bool):
    global _json_output
    _json_output = value


def set_active_profile(value: str):
    global _active_profile
    _active_profile = value


def is_json_output() -> bool:
    global _json_output
    if _json_output:
        return True
    if os.environ.get("LANSENGER_JSON", "").lower() in ("1", "true", "yes"):
        _json_output = True
        return True
    return False


def get_active_profile() -> str:
    return _active_profile


def get_store() -> CredentialStore:
    return CredentialStore(profile=_active_profile)


def get_client() -> LansengerSyncClient:
    store = CredentialStore(profile=_active_profile)
    creds = store.load_credentials()
    if not creds.get("app_id") or not creds.get("app_secret"):
        env_config = LansengerConfig.from_env()
        if env_config.is_configured():
            return LansengerSyncClient.from_config(env_config)
        rprint("[red]Error:[/red] No credentials configured for profile '{_active_profile}'. Run [bold]lansenger config set[/bold] first, or set LANSENGER_APP_ID / LANSENGER_APP_SECRET env vars.")
        raise SystemExit(1)
    config = LansengerConfig(
        app_id=creds["app_id"],
        app_secret=creds["app_secret"],
        api_gateway_url=creds.get("api_gateway_url", "https://open.e.lanxin.cn/open/apigw"),
        passport_url=creds.get("passport_url", ""),
    )
    return LansengerSyncClient.from_config(config)


def _result_to_dict(result):
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if dataclasses.is_dataclass(result):
        return dataclasses.asdict(result)
    return str(result)


def output_result(result, fields: list[str] | None = None, title: str = ""):
    if is_json_output():
        import json
        print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))
        return
    if not result.success:
        rprint(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)
    if fields:
        table = Table(title=title, show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("Field", style="bold")
        table.add_column("Value", no_wrap=True)
        for f in fields:
            val = getattr(result, f, None)
            if val is not None:
                if isinstance(val, (list, dict)):
                    import json
                    val = json.dumps(val, ensure_ascii=False) if isinstance(val, dict) else json.dumps(val, ensure_ascii=False)
                table.add_row(f, str(val))
        console.print(table)
    else:
        rprint(_result_to_dict(result))


def output_list(items: list, columns: list[str], title: str = "", row_mapper=None):
    if is_json_output():
        rprint([_result_to_dict(item) if hasattr(item, "to_dict") or dataclasses.is_dataclass(item) else item for item in items])
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