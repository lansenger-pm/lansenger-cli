import typer

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Manage personal apps/bots (4.38) - requires user_token via OAuth")


@app.command("create")
def create_personal_app(
    user_token: str = typer.Option("", "--user-token", help="User token from OAuth (required)"),
    name: str = typer.Option("", "--name", help="App name"),
    avatar_id: str = typer.Option("", "--avatar-id", help="Avatar media ID"),
    description: str = typer.Option("", "--desc", "-d", help="App description"),
):
    """Create a personal app/bot"""
    client = get_client()
    result = client.create_personal_app(
        user_token=user_token,
        name=name,
        avatar_id=avatar_id,
        description=description,
    )
    output_result(result, fields=["app_id", "secret", "apigw_addr", "passport_addr"], title="Create Personal App Result")


@app.command("update")
def update_personal_app(
    app_id: str = typer.Argument(help="App ID to update"),
    name: str = typer.Argument(help="New app name (required)"),
    user_token: str = typer.Option("", "--user-token", help="User token from OAuth (required)"),
    avatar_id: str = typer.Option("", "--avatar-id", help="Avatar media ID"),
    description: str = typer.Option("", "--desc", "-d", help="App description"),
):
    """Update a personal app/bot"""
    client = get_client()
    result = client.update_personal_app(
        app_id=app_id,
        user_token=user_token,
        name=name,
        avatar_id=avatar_id,
        description=description,
    )
    output_result(result, fields=["app_id"], title="Update Personal App Result")


@app.command("info")
def fetch_personal_app(
    app_id: str = typer.Argument(help="App ID to query"),
    user_token: str = typer.Option("", "--user-token", help="User token from OAuth (required)"),
):
    """Fetch personal app info"""
    client = get_client()
    result = client.fetch_personal_app(
        app_id=app_id,
        user_token=user_token,
    )
    output_result(result, fields=["app_id", "name", "avatar_id", "description", "apigw_addr", "passport_addr"], title="Personal App Info")


@app.command("delete")
def delete_personal_app(
    app_id: str = typer.Argument(help="App ID to delete"),
    user_token: str = typer.Option("", "--user-token", help="User token from OAuth (required)"),
):
    """Delete a personal app/bot"""
    client = get_client()
    result = client.delete_personal_app(
        app_id=app_id,
        user_token=user_token,
    )
    output_result(result, title="Delete Personal App Result")


@app.command("list")
def list_personal_apps(
    user_token: str = typer.Option("", "--user-token", help="User token from OAuth (required)"),
):
    """List personal apps/bots"""
    client = get_client()
    result = client.fetch_personal_app_list(user_token=user_token)
    if result.success and result.app_list:
        output_list(result.app_list, columns=["App ID", "Name", "Description"], row_mapper=lambda a: [
            a.get("appId", ""), a.get("appName", ""), a.get("description", ""),
        ])
    else:
        output_result(result, title="Personal App List")
