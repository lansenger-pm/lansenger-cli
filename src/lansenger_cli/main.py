import typer

from lansenger_cli.utils import get_store, output_result, is_json_output, console
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
)
from lansenger_cli.utils import set_json_output

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


@app.callback()
def global_options(
    json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON instead of formatted tables"),
):
    set_json_output(json)