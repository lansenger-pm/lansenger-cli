import typer
from rich import print as rprint

from lansenger_cli.utils import get_client, output_result

app = typer.Typer(help="OAuth2 user authentication operations")


@app.command("authorize-url")
def build_authorize_url(
    redirect_uri: str = typer.Argument(help="Redirect URI after auth"),
    scope: str = typer.Option("basic_userinfor", "--scope", "-s", help="OAuth2 scope"),
    state: str = typer.Option("", "--state", help="State parameter for CSRF protection"),
):
    client = get_client()
    url = client.build_authorize_url(redirect_uri=redirect_uri, scope=scope, state=state)
    rprint(f"[green]Authorize URL:[/green] {url}")


@app.command("exchange-code")
def exchange_code(
    code: str = typer.Argument(help="Authorization code from callback"),
    redirect_uri: str = typer.Option("", "--redirect-uri", help="Redirect URI used in authorize"),
):
    client = get_client()
    result = client.exchange_code(code=code, redirect_uri=redirect_uri)
    output_result(result, fields=[
        "user_token", "expires_in", "refresh_token",
        "refresh_expires_in", "staff_id", "scope",
    ], title="Exchange Code Result")


@app.command("refresh-token")
def refresh_user_token(
    refresh_token: str = typer.Argument(help="Refresh token"),
    scope: str = typer.Option("", "--scope", "-s", help="Scope"),
):
    client = get_client()
    result = client.refresh_user_token(refresh_token=refresh_token, scope=scope)
    output_result(result, fields=[
        "user_token", "expires_in", "refresh_token", "staff_id",
    ], title="Refresh Token Result")


@app.command("user-info")
def fetch_user_info(
    user_token: str = typer.Argument(help="User token"),
):
    client = get_client()
    result = client.fetch_user_info(user_token=user_token)
    output_result(result, fields=[
        "staff_id", "name", "org_id", "org_name",
        "mobile_phone", "email", "employee_number",
    ], title="User Info")


@app.command("parse-callback")
def parse_authorize_callback(
    query_string: str = typer.Argument(help="Query string from callback URL"),
):
    from lansenger_sdk import LansengerSyncClient
    params = LansengerSyncClient.parse_authorize_callback(query_string)
    rprint(params)


@app.command("validate-state")
def validate_callback_state(
    callback_state: str = typer.Argument(help="State from callback"),
    expected_state: str = typer.Argument(help="Expected state you set"),
):
    from lansenger_sdk import LansengerSyncClient
    valid = LansengerSyncClient.validate_callback_state(callback_state, expected_state)
    rprint(f"State valid: {valid}")