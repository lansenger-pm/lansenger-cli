import typer
import json
from rich import print as rprint

from lansenger_cli.utils import get_client, output_result, is_json_output

app = typer.Typer(help="Upload and download media files")


@app.command("upload")
def upload_media(
    file_path: str = typer.Argument(help="Local file path to upload"),
    media_type: int = typer.Option(2, "--media-type", "-t", help="1=video, 2=image, 3=audio (4.5.1 core service)"),
    user_token: str = typer.Option("", "--user-token", help="User token (optional for 4.5.1)"),
):
    """Upload media file (4.5.1 core service)"""
    client = get_client()
    result = client.upload_media(file_path=file_path, media_type=media_type, user_token=user_token)
    output_result(result, fields=["message_id", "created_time"], title="Upload Media Result (4.5.1)")


@app.command("upload-app")
def upload_app_media(
    file_path: str = typer.Argument(help="Local file path to upload"),
    media_type: str = typer.Option("file", "--media-type", "-t", help="file, video, image, audio (4.5.4 app/bot)"),
    width: int = typer.Option(0, "--width", help="Width for video/image"),
    height: int = typer.Option(0, "--height", help="Height for video/image"),
    duration: int = typer.Option(0, "--duration", help="Duration in seconds for video/audio"),
):
    """Upload media file (4.5.4 app/bot)"""
    client = get_client()
    result = client.upload_app_media(
        file_path=file_path, media_type=media_type,
        width=width or None, height=height or None, duration=duration or None,
    )
    output_result(result, fields=["message_id"], title="Upload App Media Result (4.5.4)")


@app.command("download")
def download_media(
    media_id: str = typer.Argument(help="Media ID to download"),
):
    """Download media content"""
    client = get_client()
    result = client.download_media(media_id=media_id)
    if is_json_output():
        rprint(json.dumps({"success": result.success, "size": len(result.data) if result.data else 0, "error": result.error if not result.success else ""}, ensure_ascii=False))
        return
    if result.success:
        rprint(f"[green]Downloaded media[/green] (size: {len(result.data) if result.data else 0} bytes)")
    else:
        output_result(result)


@app.command("download-to-file")
def download_media_to_file(
    media_id: str = typer.Argument(help="Media ID to download"),
    target_path: str = typer.Option("", "--output", "-o", help="Target file path"),
    media_type: str = typer.Option("file", "--media-type", help="file, image, or video"),
):
    """Download media to local file"""
    client = get_client()
    saved_path = client.download_media_to_file(
        media_id=media_id, target_path=target_path, media_type=media_type,
    )
    if is_json_output():
        rprint(json.dumps({"saved_path": saved_path}, ensure_ascii=False))
        return
    rprint(f"[green]Saved to:[/green] {saved_path}")


@app.command("path")
def fetch_media_path(
    media_id: str = typer.Argument(help="Media ID to get path for"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch media path/URL"""
    client = get_client()
    result = client.fetch_media_path(media_id=media_id, user_token=user_token)
    output_result(result, fields=["media_path", "name", "type", "size"], title="Media Path Result")
