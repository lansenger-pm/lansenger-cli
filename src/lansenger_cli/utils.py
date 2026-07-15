import os
import time
import dataclasses
import logging

from lansenger_sdk import LansengerSyncClient, CredentialStore, LansengerConfig, LansengerAuthError
from rich import print as rprint
from rich.console import Console
from rich.table import Table

console = Console()
_json_output = False
_active_profile = "default"
_as_staff_id = ""
_app_token = ""
_user_token = ""
_verbose = False

_formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
_handler = logging.StreamHandler()
_handler.setFormatter(_formatter)


def set_verbose(value: bool):
    global _verbose
    _verbose = value
    if value:
        root = logging.getLogger("lansenger_sdk")
        root.setLevel(logging.DEBUG)
        if _handler not in root.handlers:
            root.addHandler(_handler)
        root.propagate = False
    else:
        root = logging.getLogger("lansenger_sdk")
        root.setLevel(logging.WARNING)
        if _handler in root.handlers:
            root.removeHandler(_handler)


def is_verbose() -> bool:
    return _verbose


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


def set_as_staff_id(value: str):
    global _as_staff_id
    _as_staff_id = value


def get_as_staff_id() -> str:
    return _as_staff_id


def set_app_token(value: str):
    global _app_token
    _app_token = value


def get_app_token() -> str:
    return _app_token


def set_user_token(value: str):
    global _user_token
    _user_token = value


def get_user_token() -> str:
    return _user_token


class _AutoUserTokenProxy:
    """Proxy that auto-injects userToken from CredentialStore for --as mode.

    Intercepts method calls on the client and replaces empty user_token
    kwargs with the stored & auto-refreshed token for the given staff_id.

    Only activates when the caller passes user_token="" — explicit
    --user-token values are never overridden.
    """

    def __init__(self, raw_client, store, staff_id):
        self._client = raw_client
        self._store = store
        self._staff_id = staff_id

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            if "user_token" in kwargs and not kwargs.get("user_token"):
                kwargs["user_token"] = _load_and_refresh_user_token(
                    self._store, self._staff_id
                )
            return attr(*args, **kwargs)

        return wrapper


def _load_and_refresh_user_token(store: CredentialStore, staff_id: str) -> str:
    """Load userToken from store for staff_id, auto-refreshing if expired."""
    cached = store.load_user_token(staff_id=staff_id)
    user_token = cached.get("user_token", "")
    refresh_token = cached.get("refresh_token", "")
    expiry = cached.get("user_token_expiry", 0)

    if user_token and expiry > time.time():
        return user_token

    if not refresh_token:
        raise LansengerAuthError(
            f"No userToken available for staff_id={staff_id} and no refreshToken for auto-refresh. "
            "Run OAuth2 authorize flow: build_authorize_url → exchange_code."
        )

    # Use a raw client (no proxy) to avoid infinite recursion
    client = _create_raw_client()
    result = client.refresh_user_token(refresh_token=refresh_token)
    if not result.success:
        raise LansengerAuthError(f"userToken refresh failed for staff_id={staff_id}: {result.error}")

    store.save_user_token(
        result.user_token,
        result.refresh_token or refresh_token,
        result.expires_in,
        300,
        result.refresh_expires_in or 0,
        staff_id=result.staff_id or staff_id,
    )
    return result.user_token


def get_store() -> CredentialStore:
    return CredentialStore(profile=_active_profile)


def _create_raw_client() -> LansengerSyncClient:
    """Create a base LansengerSyncClient without proxy wrapping.

    Supports two modes:
    - External mode (--app-token provided): creates client with the
      provided token only. No credential file or env vars needed.
      Token refresh is disabled — the caller manages token lifecycle.
    - Normal mode: reads credentials from store file or env vars.
    """
    # External mode: just app_token + user_token, no credential file needed
    if _app_token:
        config = LansengerConfig(
            app_id="",
            app_secret="",
            api_gateway_url=os.environ.get(
                "LANSENGER_API_GATEWAY_URL", ""
            ),
            app_token=_app_token,
            user_token=_user_token,
        )
        return LansengerSyncClient.from_config(config)

    store = CredentialStore(profile=_active_profile)
    creds = store.load_credentials()
    if not creds.get("app_id") or not creds.get("app_secret"):
        env_config = LansengerConfig.from_env()
        if env_config.is_configured():
            return LansengerSyncClient.from_config(env_config)
        rprint(f"[red]Error:[/red] No credentials configured for profile '{_active_profile}'. Run [bold]lansenger config set[/bold] first, or set LANSENGER_APP_ID / LANSENGER_APP_SECRET env vars, or use [bold]--app-token[/bold] for external token mode.")
        raise SystemExit(1)
    config = LansengerConfig(
        app_id=creds["app_id"],
        app_secret=creds["app_secret"],
        api_gateway_url=creds.get("api_gateway_url", ""),
        passport_url=creds.get("passport_url", ""),
        redirect_uri=creds.get("redirect_uri", ""),
        app_token=_app_token,
    )
    return LansengerSyncClient.from_config(config)


def get_client():
    """Get a LansengerSyncClient, wrapped in proxy when --as is set.

    When --as <staff_id> is active, returns an _AutoUserTokenProxy that
    auto-injects the stored & auto-refreshed userToken for that staff_id
    into any method call where user_token="" is passed (i.e., the caller
    did not provide an explicit --user-token).
    """
    raw = _create_raw_client()
    if _as_staff_id:
        store = CredentialStore(profile=_active_profile)
        return _AutoUserTokenProxy(raw, store, _as_staff_id)
    return raw


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