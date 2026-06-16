import typer
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from rich import print as rprint
from rich.console import Console

from lansenger_cli.utils import get_client, get_store, output_result, is_json_output

console = Console()
app = typer.Typer(help="OAuth2 user authentication operations")


@app.command("authorize-url")
def build_authorize_url(
    redirect_uri: str = typer.Argument(help="Redirect URI after auth"),
    scope: str = typer.Option("basic_userinfor", "--scope", "-s", help="OAuth2 scope"),
    state: str = typer.Option("", "--state", help="State parameter for CSRF protection"),
):
    """Build OAuth2 authorization URL"""
    client = get_client()
    url = client.build_authorize_url(redirect_uri=redirect_uri, scope=scope, state=state or None)
    if is_json_output():
        rprint(json.dumps({"authorize_url": url}, ensure_ascii=False))
        return
    rprint(f"[green]Authorize URL:[/green] {url}")


@app.command("exchange-code")
def exchange_code(
    code: str = typer.Argument(help="Authorization code from callback"),
    redirect_uri: str = typer.Option("", "--redirect-uri", help="Redirect URI used in authorize"),
):
    """Exchange authorization code for user token"""
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
    """Refresh user token using refresh token"""
    client = get_client()
    result = client.refresh_user_token(refresh_token=refresh_token, scope=scope)
    if result.success and result.user_token:
        store = get_store()
        store.save_user_token(
            result.user_token,
            result.refresh_token or refresh_token,
            result.expires_in,
            300,  # margin
            result.refresh_expires_in or 0,  # refresh_expires_in
            staff_id=result.staff_id or "",
        )
    output_result(result, fields=[
        "user_token", "expires_in", "refresh_token", "staff_id",
    ], title="Refresh Token Result")


@app.command("user-info")
def fetch_user_info(
    user_token: str = typer.Argument(help="User token"),
):
    """Fetch user information using user token"""
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
    """Parse OAuth2 callback query string"""
    from lansenger_sdk import LansengerSyncClient
    params = LansengerSyncClient.parse_authorize_callback(query_string)
    if is_json_output():
        rprint(json.dumps(params, ensure_ascii=False))
        return
    rprint(params)


@app.command("validate-state")
def validate_callback_state(
    callback_state: str = typer.Argument(help="State from callback"),
    expected_state: str = typer.Argument(help="Expected state you set"),
):
    """Validate OAuth2 callback state"""
    from lansenger_sdk import LansengerSyncClient
    valid = LansengerSyncClient.validate_callback_state(callback_state, expected_state)
    if is_json_output():
        rprint(json.dumps({"valid": valid}, ensure_ascii=False))
        return
    rprint(f"State valid: {valid}")


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        code = params.get("code", [""])[0]
        state = params.get("state", [""])[0]
        error = params.get("error", [""])[0]

        if error:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"OAuth2 error: {error}".encode())
            self.server._callback_result = {"error": error}
        elif code:
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Authorization successful. You can close this tab.".encode())
            self.server._callback_result = {"code": code, "state": state}
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("Missing code parameter.".encode())
            self.server._callback_result = {"error": "missing_code"}

    def log_message(self, format, *args):
        pass


@app.command("local-callback")
def local_callback(
    port: int = typer.Option(8765, "--port", "-p", help="Local HTTP server port"),
    scope: str = typer.Option("basic_userinfor", "--scope", "-s", help="OAuth2 scope"),
    state: str = typer.Option("", "--state", help="CSRF state (auto-generated if empty)"),
    auto_exchange: bool = typer.Option(True, "--exchange/--no-exchange", "-E", help="Auto-exchange code for userToken"),
    timeout: int = typer.Option(120, "--timeout", "-t", help="Max wait seconds for callback"),
    redirect_uri: str = typer.Option("", "--redirect-uri", help="Override redirect_uri (default: http://localhost:<port>)"),
):
    """Start a local HTTP server to capture OAuth2 callback and auto-exchange the code.

    Workflow:
    1. Starts a temporary HTTP server on localhost:<port>
    2. Prints the authorize URL — open it in a browser to authorize
    3. Browser redirects back to localhost with the auth code
    4. Local server captures the code, auto-exchanges for userToken
    5. Saves credentials and shuts down the server

    Examples:
        lansenger oauth local-callback
        lansenger oauth local-callback --port 9999
        lansenger oauth local-callback --redirect-uri https://your-trusted-domain.com
    """
    if not redirect_uri:
        redirect_uri = f"http://localhost:{port}"

    client = get_client()
    auth_url = client.build_authorize_url(redirect_uri=redirect_uri, scope=scope, state=state or None)

    if not is_json_output():
        rprint("[green]Authorize URL — open in browser:[/green]")
        rprint(auth_url)
        rprint(f"\n[yellow]Waiting for callback on port {port}...[/yellow] (timeout: {timeout}s)")
        rprint(f"[dim]redirect_uri={redirect_uri}[/dim]")
    else:
        rprint(json.dumps({"authorize_url": auth_url, "redirect_uri": redirect_uri, "port": port}, ensure_ascii=False))

    class _ReuseAddrHTTPServer(HTTPServer):
        allow_reuse_address = True
        allow_reuse_port = True

    server = _ReuseAddrHTTPServer(("localhost", port), _OAuthCallbackHandler)
    server._callback_result = None
    server.timeout = 1

    start_time = time.time()
    while server._callback_result is None and (time.time() - start_time) < timeout:
        server.handle_request()

    server.server_close()

    if server._callback_result is None:
        rprint("[red]Timeout: no callback received within {}s[/red]".format(timeout))
        raise typer.Exit(1)

    result = server._callback_result
    if "error" in result:
        rprint(f"[red]OAuth2 error: {result['error']}[/red]")
        raise typer.Exit(1)

    code = result["code"]
    received_state = result["state"]

    if not is_json_output():
        rprint(f"[green]Received code:[/green] {code}")
        rprint(f"[green]Received state:[/green] {received_state}")

    if auto_exchange:
        exchange_result = client.exchange_code(code=code, redirect_uri=redirect_uri)
        if exchange_result.success and exchange_result.user_token:
            store = get_store()
            existing = store.load_user_token()
            rt = exchange_result.refresh_token or existing.get("refresh_token", "")
            store.save_user_token(
                exchange_result.user_token, rt,
                exchange_result.expires_in, 300,
                exchange_result.refresh_expires_in or 0,
                staff_id=exchange_result.staff_id or "",
            )
        output_result(exchange_result, fields=[
            "user_token", "expires_in", "refresh_token",
            "refresh_expires_in", "staff_id", "scope",
        ], title="Exchange Code Result")
    else:
        if is_json_output():
            rprint(json.dumps({"code": code, "state": received_state}, ensure_ascii=False))
        else:
            rprint(f"\n[cyan]Use this code to exchange manually:[/cyan]")
            rprint(f"  lansenger oauth exchange-code {code} --redirect-uri {redirect_uri}")