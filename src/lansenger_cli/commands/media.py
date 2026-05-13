import typer

from lansenger_cli.utils import get_client, output_result

app = typer.Typer(help="Upload and download media files")


@app.command("upload")
def upload_media(
    file_path: str = typer.Argument(help="Local file path to upload"),
    media_type: int = typer.Option(3, "--media-type", "-t", help="1=video, 2=image, 3=file"),
):
    client = get_client()
    result = client.upload_media(file_path=file_path, media_type=media_type)
    output_result(result, fields=["message_id"], title="Upload Media Result")


@app.command("download")
def download_media(
    media_id: str = typer.Argument(help="Media ID to download"),
):
    client = get_client()
    result = client.download_media(media_id=media_id)
    if result.success:
        from rich import print as rprint
        rprint(f"[green]Downloaded media[/green] (size: {len(result.data) if result.data else 0} bytes)")
    else:
        output_result(result)


@app.command("download-to-file")
def download_media_to_file(
    media_id: str = typer.Argument(help="Media ID to download"),
    target_path: str = typer.Option("", "--output", "-o", help="Target file path"),
    media_type: str = typer.Option("file", "--media-type", help="file, image, or video"),
):
    client = get_client()
    saved_path = client.download_media_to_file(
        media_id=media_id, target_path=target_path, media_type=media_type,
    )
    from rich import print as rprint
    rprint(f"[green]Saved to:[/green] {saved_path}")