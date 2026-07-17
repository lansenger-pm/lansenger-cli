import typer
from rich import print as rprint
import json

from lansenger_cli.utils import get_client, is_json_output

app = typer.Typer(help="Health check and connection verification")


@app.command("check")
def health_check():
    """Check Lansenger API connection health"""
    client = get_client()
    result = client.health_check()
    if is_json_output():
        rprint(json.dumps({"healthy": result}, ensure_ascii=False))
        return
    if result:
        rprint("[green]OK[/green] — Lansenger connection is healthy (app token obtained successfully)")
    else:
        rprint("[red]FAIL[/red] — Could not obtain app token. Check your credentials.")
        raise typer.Exit(1)
