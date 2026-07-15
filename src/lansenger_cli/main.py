import typer

from importlib.metadata import version as pkg_version
from lansenger_cli.utils import get_store, output_result, is_json_output, console
from lansenger_cli.utils import set_json_output, set_active_profile, get_active_profile, set_as_staff_id, set_app_token, set_user_token, set_verbose
from lansenger_cli.commands import (
    config as config_cmd,
    message as message_cmd,
    group as group_cmd,
    staff as staff_cmd,
    department as department_cmd,
    calendar as calendar_cmd,
    todo as todo_cmd,
    oauth as oauth_cmd,
    callback as callback_cmd,
    media as media_cmd,
    streaming as streaming_cmd,
    health as health_cmd,
    chat as chat_cmd,
    bot_command as bot_command_cmd,
    personal_app as personal_app_cmd,
)

app = typer.Typer(
    name="lansenger",
    help="Lansenger (蓝信) CLI — interact with Lansenger APIs from the command line.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(config_cmd.app, name="config")
app.add_typer(message_cmd.app, name="message")
app.add_typer(group_cmd.app, name="group")
app.add_typer(staff_cmd.app, name="staff")
app.add_typer(department_cmd.app, name="department")
app.add_typer(calendar_cmd.app, name="calendar")
app.add_typer(todo_cmd.app, name="todo")
app.add_typer(oauth_cmd.app, name="oauth")
app.add_typer(callback_cmd.app, name="callback")
app.add_typer(media_cmd.app, name="media")
app.add_typer(streaming_cmd.app, name="streaming")
app.add_typer(chat_cmd.app, name="chat")
app.add_typer(health_cmd.app, name="health")
app.add_typer(bot_command_cmd.app, name="bot-command")
app.add_typer(personal_app_cmd.app, name="personal-app")


@app.callback(invoke_without_command=True)
def global_options(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON instead of formatted tables"),
    profile: str = typer.Option("default", "--profile", "-P", help="Credential profile to use"),
    as_user: str = typer.Option("", "--as", help="Act as a specific user (staff_id). Auto-loads & refreshes stored userToken."),
    app_token: str = typer.Option("", "--app-token", help="App access token (external mode — no auto-refresh)"),
    user_token: str = typer.Option("", "--user-token", help="User access token (external mode — no auto-refresh)"),
    version: bool = typer.Option(False, "--version", "-v", help="Show CLI and SDK versions"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging"),
):
    set_json_output(json)
    set_active_profile(profile)
    set_as_staff_id(as_user)
    set_app_token(app_token)
    set_user_token(user_token)
    if verbose:
        set_verbose(True)
    if version:
        cli_ver = pkg_version("lansenger-cli")
        sdk_ver = pkg_version("lansenger-sdk")
        if is_json_output():
            console.print_json(data={"cli_version": cli_ver, "sdk_version": sdk_ver})
        else:
            console.print(f"lansenger-cli {cli_ver} (SDK {sdk_ver})")
        raise typer.Exit()
    if not ctx.invoked_subcommand:
        ctx.get_help()
        raise typer.Exit()
