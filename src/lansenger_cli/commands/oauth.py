import typer
import json
import subprocess
import sys
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from rich import print as rprint
from rich.console import Console

from lansenger_cli import qr
from lansenger_cli.utils import EXIT_ERROR, get_active_profile, get_client, get_store, is_json_output, output_result

console = Console()
app = typer.Typer(help="OAuth2 user authentication operations")

_sleep = time.sleep  # patchable for tests (device flow polling)
_monotonic = time.monotonic  # patchable for tests (deadline checks)


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    try:
        import platform
        system = platform.system()
        if system == "Darwin":
            subprocess.run("pbcopy", input=text, text=True, capture_output=True, check=True)
        elif system == "Windows":
            subprocess.run("clip", input=text, text=True, capture_output=True, check=True)
        else:
            subprocess.run(["wl-copy"], input=text, text=True, capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _stdout_is_utf8() -> bool:
    return "utf" in (getattr(sys.stdout, "encoding", "") or "").lower()


def _print_device_qr(uri: str, mode: str, png_path: str = "", data_uri: bool = False, ecc: str = "M") -> str:
    """Print a scannable QR for the device verification URL (and/or save it as PNG).

    Returns a base64 PNG data: URI when ``data_uri`` is set, so a caller can hand the QR
    to a panel that cannot render terminal text or read local files.
    """
    if not uri:
        return ""
    if ecc not in ("L", "M"):
        rprint(f"[red]--qr-ecc 只支持 L / M（收到 {ecc}）[/red]")
        raise typer.Exit(1)
    matrix = qr.encode(uri, ecc=ecc)
    if png_path:
        target = Path(png_path).expanduser()
        target.write_bytes(qr.to_png(matrix))
        note = f"（二维码已保存到 {target} · {len(matrix)}x{len(matrix)} 模块）"
        if is_json_output():
            print(note, file=sys.stderr)
        else:
            console.print(note, style="dim")
    if mode != "none" and not is_json_output():
        use_unicode = mode == "utf8" or (mode == "auto" and _stdout_is_utf8())
        console.print(qr.render_text(matrix, unicode=use_unicode), style="black on white", soft_wrap=True, highlight=False)
    return qr.to_data_uri(matrix) if data_uri else ""


def _emit_qr_data_uri(data_uri: str) -> None:
    """Hand the QR to a panel: a stderr JSON event in --json mode, a plain URI otherwise."""
    if not data_uri:
        return
    if is_json_output():
        print(json.dumps({"event": "device_qr", "format": "png", "qr_data_uri": data_uri}, ensure_ascii=False), file=sys.stderr)
    else:
        console.print(data_uri, soft_wrap=True, highlight=False)


def _fail_fast_credentials() -> None:
    """Abort a device login before the user scans when the profile cannot get an appToken.

    The last step of a device login exchanges the OAuth2 code through the API gateway, which
    needs an appToken (app_id + app_secret). Without working credentials the user would scan,
    approve, and still get nothing, so the check runs before the device code is requested.
    """
    message = "cannot obtain an appToken with the active profile credentials; the token exchange of this device login would fail"
    hint = f"lansenger config set app_secret <new-secret> -P {get_active_profile()}"
    if is_json_output():
        print(json.dumps({"ok": False, "error": {"type": "auth_failed", "message": message}, "hint": hint}, ensure_ascii=False), file=sys.stderr)
    else:
        rprint("[red]凭据自检失败：[/red]当前 profile 的 app_id/app_secret 换不到 appToken，即使手机端确认也无法完成兑换。")
        rprint(f"[dim]修复：{hint}（或检查 app_id / api_gateway_url）[/dim]")
    raise typer.Exit(1)


def _fail_exchange(exc: Exception) -> None:
    """Report a failed token exchange as a structured CLI error instead of a traceback."""
    message = f"{type(exc).__name__}: {exc}"
    hint = f"lansenger config set app_secret <new-secret> -P {get_active_profile()}"
    if is_json_output():
        print(json.dumps({"ok": False, "error": {"type": "exchange_failed", "message": message}, "hint": hint}, ensure_ascii=False), file=sys.stderr)
    else:
        rprint(f"[red]兑换 token 失败：[/red]{message}")
        rprint("[dim]手机端授权已通过，只有最后一步兑换失败。[/dim]")
        rprint(f"[dim]修复：{hint}（或检查 app_id / api_gateway_url）[/dim]")
    raise typer.Exit(1)


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
    if _copy_to_clipboard(url):
        rprint("[dim]  (copied to clipboard)[/dim]")


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
            rprint("\n[cyan]Use this code to exchange manually:[/cyan]")
            rprint(f"  lansenger oauth exchange-code {code} --redirect-uri {redirect_uri}")


# --- OAuth2 device flow (新版开平；旧版自动降级，见 docs/action-boundary.md) ---


@app.command("device-authorize")
def device_authorize(
    client_id: str = typer.Option("", "--client-id", help="OAuth2 clientId（默认取 app_id）"),
    source: str = typer.Option("CLI", "--from", help="客户端来源：AutoClaw/CLI/OpenClaw/MCP"),
    qr_mode: str = typer.Option("auto", "--qr", help="是否打印可扫二维码：auto/utf8/ascii/none"),
    qr_png: str = typer.Option("", "--qr-png", help="把二维码写入该 PNG 文件（--json 模式下也可用）"),
    qr_data_uri: bool = typer.Option(False, "--qr-data-uri", help="以 data: URI 输出二维码（供会话/网页面板嵌入）"),
    qr_ecc: str = typer.Option("M", "--qr-ecc", help="二维码纠错等级：M（默认，容量大）/ L"),
):
    """申请设备码（设备码流程第 1 步）：只申请码，不等待手机端确认。"""
    client = get_client()
    result = client.request_device_authorization(client_id=client_id, source=source)
    if not result.success:
        if not is_json_output() and result.error_type == "deviceflow_unsupported":
            rprint("[dim]回退：lansenger oauth authorize-url <redirect_uri>  |  lansenger oauth local-callback[/dim]")
        output_result(result, fields=["error", "error_type"], title="设备码申请失败")
    if is_json_output():
        output_result(
            result,
            fields=[
                "device_code", "user_code", "verification_uri_complete",
                "interval", "expires_in", "expires_at", "open_api_domain",
            ],
            title="Device Authorization",
        )
        _emit_qr_data_uri(_print_device_qr(result.verification_uri_complete, qr_mode, qr_png, qr_data_uri, qr_ecc))
        return
    rprint("[green]请用蓝信手机端扫描下面的二维码，并在手机端确认：[/green]")
    rprint(f"[green]  用户码（手机端会显示，用于核对）:[/green] [bold]{result.user_code}[/bold]")
    _emit_qr_data_uri(_print_device_qr(result.verification_uri_complete, qr_mode, qr_png, qr_data_uri, qr_ecc))
    rprint("[yellow]本命令只申请设备码：不等待确认，也不会完成登录。[/yellow]")
    rprint("[dim]  扫码后自动完成登录： lansenger oauth device-login[/dim]")
    rprint(f"[dim]  用设备码继续等待：   lansenger oauth device-poll {result.device_code} --wait[/dim]")
    rprint(f"[dim]  链接 {result.verification_uri_complete} · 有效期 {result.expires_in}s[/dim]")
    if _copy_to_clipboard(result.verification_uri_complete):
        rprint("[dim]（链接已复制到剪贴板）[/dim]")


_POLL_LABELS = {
    "authorization_pending": "等待手机端确认",
    "access_approved": "已确认（可兑换 token）",
    "access_denied": "用户在手机端拒绝",
    "expired_token": "设备码已过期",
}


@app.command("device-poll")
def device_poll(
    device_code: str = typer.Argument(help="device-authorize 返回的 deviceCode"),
    client_id: str = typer.Option("", "--client-id", help="OAuth2 clientId（默认取 app_id）"),
    wait: bool = typer.Option(False, "--wait", help="每 5 秒轮询一次，直到确认/拒绝/过期"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="--wait 时最长等待秒数"),
):
    """轮询一次（或 --wait 持续轮询）设备码授权结果：本命令不会替用户在手机端确认。

    退出码：0 = 等待中/已确认（确认时带 oauth2_code），1 = 拒绝/过期/错误。
    脚本建议单次轮询 + 自己控制循环。
    """
    client = get_client()
    deadline = _monotonic() + timeout
    try:
        while True:
            result = client.poll_device_token(device_code, client_id=client_id)
            if not (result.success and result.state == "authorization_pending" and wait):
                break
            if _monotonic() >= deadline:
                if is_json_output():
                    print(json.dumps({"ok": False, "error": {"type": "timeout", "message": f"still pending after {timeout}s"}}, ensure_ascii=False), file=sys.stderr)
                else:
                    rprint(f"[red]超时（timeout）：{timeout}s 内仍未被手机端确认（still pending）[/red]")
                raise typer.Exit(1)
            _sleep(5)
    except KeyboardInterrupt:
        if is_json_output():
            print(json.dumps({"ok": False, "error": {"type": "cancelled", "message": "interrupted by user"}}, ensure_ascii=False), file=sys.stderr)
        else:
            rprint("[red]已取消（cancelled）[/red]")
        raise typer.Exit(1) from None
    if is_json_output():
        output_result(result, fields=["state", "oauth2_code"], title="Device Poll")
    else:
        label = _POLL_LABELS.get(result.state or "", result.state or "未知状态")
        rprint(f"[green]状态：[/green]{label}（{result.state}）")
        if result.oauth2_code:
            rprint(f"[dim]oauth2_code：{result.oauth2_code}（可用 lansenger oauth exchange-code 兑换）[/dim]")
        if result.error:
            rprint(f"[red]错误：[/red]{result.error}")
        if not result.success:
            raise SystemExit(EXIT_ERROR)


@app.command("device-login")
def device_login(
    client_id: str = typer.Option("", "--client-id", help="OAuth2 clientId（默认取 app_id）"),
    source: str = typer.Option("CLI", "--from", help="客户端来源：AutoClaw/CLI/OpenClaw/MCP"),
    no_browser: bool = typer.Option(False, "--no-browser", help="已废弃：默认不再打开浏览器"),
    open_browser: bool = typer.Option(False, "--open-browser", help="额外在本机浏览器打开授权链接"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="等待手机端确认的最长秒数"),
    qr_mode: str = typer.Option("auto", "--qr", help="是否打印可扫二维码：auto/utf8/ascii/none"),
    qr_png: str = typer.Option("", "--qr-png", help="把二维码写入该 PNG 文件（--json 模式下也可用）"),
    qr_data_uri: bool = typer.Option(False, "--qr-data-uri", help="以 data: URI 输出二维码（供会话/网页面板嵌入）"),
    qr_ecc: str = typer.Option("M", "--qr-ecc", help="二维码纠错等级：M（默认，容量大）/ L"),
):
    """设备码一键登录：申请 → 显示二维码 → 等用户在蓝信手机端确认 → 兑换 → 落库。

    适用于无头/远程主机（不需要本地回调服务）；旧版开放平台不支持设备码时
    退出码 1 并给出回退提示。确认动作由用户在手机端完成，CLI 不会代为确认。
    """
    client = get_client()
    if not client.health_check():
        _fail_fast_credentials()
    auth = client.request_device_authorization(client_id=client_id, source=source)
    if not auth.success:
        if not is_json_output() and auth.error_type == "deviceflow_unsupported":
            rprint("[dim]回退：lansenger oauth authorize-url <redirect_uri>  |  lansenger oauth local-callback[/dim]")
        output_result(auth, fields=["error", "error_type"], title="设备码申请失败")

    interval = max(1, auth.interval or 5)
    deadline = _monotonic() + timeout
    uri = auth.verification_uri_complete
    if is_json_output():
        event = {
            "event": "device_authorization",
            "device_code": auth.device_code,
            "user_code": auth.user_code,
            "verification_uri_complete": uri,
            "interval": interval,
            "expires_in": auth.expires_in,
        }
        if qr_data_uri and uri:
            event["qr_data_uri"] = qr.to_data_uri(qr.encode(uri, ecc=qr_ecc))
        print(json.dumps(event, ensure_ascii=False), file=sys.stderr)
        _print_device_qr(uri, qr_mode, qr_png, False, qr_ecc)
    else:
        rprint("[green]1. 请用蓝信手机端扫描下面的二维码，并在手机端点击确认：[/green]")
        rprint(f"[green]   用户码:[/green] [bold]{auth.user_code}[/bold]")
        if _copy_to_clipboard(uri):
            rprint("[dim]（链接已复制到剪贴板）[/dim]")
        _emit_qr_data_uri(_print_device_qr(uri, qr_mode, qr_png, qr_data_uri, qr_ecc))
        rprint(f"[dim]   链接: {uri}[/dim]")
        rprint("[yellow]2. 等待手机端确认…[/yellow]（Ctrl+C 取消）")
    if open_browser and not no_browser and uri:
        try:
            webbrowser.open(uri)
        except Exception:
            pass

    poll = None
    try:
        while True:
            if _monotonic() >= deadline:
                if is_json_output():
                    print(json.dumps({"ok": False, "error": {"type": "timeout", "message": f"timeout after {timeout}s"}}, ensure_ascii=False), file=sys.stderr)
                else:
                    rprint(f"[red]超时（timeout）：{timeout}s 内未收到手机端确认[/red]")
                raise typer.Exit(1)
            poll = client.poll_device_token(auth.device_code, client_id=client_id)
            if poll.success and poll.state == "authorization_pending":
                _sleep(interval)
                continue
            break
    except KeyboardInterrupt:
        if is_json_output():
            print(json.dumps({"ok": False, "error": {"type": "cancelled", "message": "interrupted by user"}}, ensure_ascii=False), file=sys.stderr)
        else:
            rprint("[red]已取消（cancelled）[/red]")
        raise typer.Exit(1) from None

    if not poll.success:
        if not is_json_output() and poll.error_type == "deviceflow_unsupported":
            rprint("[dim]回退：lansenger oauth authorize-url <redirect_uri>  |  lansenger oauth local-callback[/dim]")
        if is_json_output():
            output_result(poll, fields=["state", "error"], title="Device Approval")
        else:
            label = _POLL_LABELS.get(poll.state or "", poll.state or "未知状态")
            rprint(f"[red]未完成登录：[/red]{label}（{poll.state}）{poll.error or ''}")
            raise SystemExit(EXIT_ERROR)
    if not is_json_output():
        rprint("[green]✓ 手机端已确认，正在兑换 token…[/green]")

    try:
        exchange = client.exchange_code(code=poll.oauth2_code)
    except Exception as exc:  # credential/network failures from the SDK surface as a structured CLI error
        _fail_exchange(exc)
    if exchange.success and exchange.user_token:
        store = get_store()
        existing = store.load_user_token()
        rt = exchange.refresh_token or existing.get("refresh_token", "")
        store.save_user_token(
            exchange.user_token, rt,
            exchange.expires_in, 300,
            exchange.refresh_expires_in or 0,
            staff_id=exchange.staff_id or "",
        )
        if not is_json_output():
            rprint(f"[green]✓ 登录完成：[/green]staff_id={exchange.staff_id or '-'} · userToken 有效期 {exchange.expires_in}s · refresh 有效期 {exchange.refresh_expires_in or 0}s")
    if is_json_output():
        output_result(
            exchange,
            fields=["user_token", "expires_in", "refresh_token", "refresh_expires_in", "staff_id", "scope"],
            title="Device Login",
        )
    elif not exchange.success:
        rprint(f"[red]兑换 token 失败：[/red]{exchange.error or '未知错误'}")
        raise SystemExit(EXIT_ERROR)
