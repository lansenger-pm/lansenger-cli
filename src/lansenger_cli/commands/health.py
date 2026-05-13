import typer
from rich import print as rprint

from lansenger_cli.utils import get_client

app = typer.Typer(help="Health check and connection verification")


@app.command("check")
def health_check():
    client = get_client()
    result = client.health_check()
    if result:
        rprint("[green]OK[/green] — Lansenger connection is healthy (app token obtained successfully)")
    else:
        rprint("[red]FAIL[/red] — Could not obtain app token. Check your credentials.")
        raise typer.Exit(1)