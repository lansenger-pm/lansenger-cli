import typer

from lansenger_cli.utils import get_client, output_result

app = typer.Typer(help="Streaming message operations (for AI agent progressive output)")


@app.command("create")
def create_stream_message(
    receiver_id: str = typer.Argument(help="Receiver ID"),
    receiver_type: str = typer.Argument(help="Receiver type: single or group"),
    stream_id: str = typer.Argument(help="Stream ID (unique per session)"),
):
    client = get_client()
    result = client.create_stream_message(
        receiver_id=receiver_id, receiver_type=receiver_type, stream_id=stream_id,
    )
    output_result(result, fields=["message_id"], title="Create Stream Message Result")


@app.command("fetch")
def fetch_stream_message(
    msg_id: str = typer.Argument(help="Message ID of the stream message"),
):
    client = get_client()
    result = client.fetch_stream_message(msg_id=msg_id)
    output_result(result, fields=["message_id"], title="Fetch Stream Message Result")