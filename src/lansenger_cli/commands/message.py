import typer
from typing import Optional, List

from lansenger_cli.utils import get_client, output_result, output_list

app = typer.Typer(help="Send and manage messages")


@app.command("send-text")
def send_text(
    chat_id: str = typer.Argument(help="Chat ID (user/group)"),
    content: str = typer.Argument(help="Text content"),
    file_path: str = typer.Option("", "--file", "-f", help="File path to attach"),
    is_group: bool = typer.Option(False, "--group", "-g", help="Send as group message"),
    reminder_all: bool = typer.Option(False, "--mention-all", help="@all in group"),
    reminder_user_ids: Optional[List[str]] = typer.Option(None, "--mention", help="User IDs to @mention"),
    user_token: str = typer.Option("", "--user-token", help="User token for private channel"),
    sender_id: str = typer.Option("", "--sender-id", help="Sender staff ID for group message"),
):
    client = get_client()
    result = client.send_text(
        chat_id=chat_id,
        content=content,
        file_path=file_path,
        is_group=is_group,
        reminder_all=reminder_all,
        reminder_user_ids=reminder_user_ids,
        user_token=user_token,
        sender_id=sender_id,
    )
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send Text Result")


@app.command("send-markdown")
def send_markdown(
    chat_id: str = typer.Argument(help="Chat ID"),
    content: str = typer.Argument(help="Markdown content"),
):
    client = get_client()
    result = client.send_markdown(chat_id=chat_id, content=content)
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send Markdown Result")


@app.command("send-file")
def send_file(
    chat_id: str = typer.Argument(help="Chat ID"),
    file_path: str = typer.Argument(help="Local file path"),
    caption: str = typer.Option("", "--caption", "-c", help="Caption text"),
    media_type: Optional[int] = typer.Option(None, "--media-type", help="1=video, 2=image, 3=file"),
):
    client = get_client()
    result = client.send_file(
        chat_id=chat_id,
        file_path=file_path,
        caption=caption,
        media_type=media_type,
    )
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send File Result")


@app.command("send-image-url")
def send_image_url(
    chat_id: str = typer.Argument(help="Chat ID"),
    image_url: str = typer.Argument(help="Image URL to send"),
    caption: str = typer.Option("", "--caption", "-c", help="Caption text"),
):
    client = get_client()
    result = client.send_image_url(chat_id=chat_id, image_url=image_url, caption=caption)
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send Image Result")


@app.command("send-link-card")
def send_link_card(
    chat_id: str = typer.Argument(help="Chat ID"),
    title: str = typer.Argument(help="Card title"),
    link: str = typer.Argument(help="Card link URL"),
    description: str = typer.Option("", "--desc", "-d", help="Card description"),
    icon_link: str = typer.Option("", "--icon", help="Icon URL"),
    pc_link: str = typer.Option("", "--pc-link", help="PC link URL"),
    from_name: str = typer.Option("", "--from-name", help="Source name"),
    from_icon_link: str = typer.Option("", "--from-icon", help="Source icon URL"),
):
    client = get_client()
    result = client.send_link_card(
        chat_id=chat_id, title=title, link=link,
        description=description, icon_link=icon_link,
        pc_link=pc_link, from_name=from_name, from_icon_link=from_icon_link,
    )
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send Link Card Result")


@app.command("send-app-articles")
def send_app_articles(
    chat_id: str = typer.Argument(help="Chat ID"),
    articles: List[str] = typer.Argument(help="Articles as JSON dicts, e.g. '{\"title\":\"T\",\"url\":\"U\"}'"),
):
    import json
    parsed = [json.loads(a) for a in articles]
    client = get_client()
    result = client.send_app_articles(chat_id=chat_id, articles=parsed)
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send App Articles Result")


@app.command("send-app-card")
def send_app_card(
    chat_id: str = typer.Argument(help="Chat ID"),
    body_title: str = typer.Argument(help="Card body title"),
    head_title: str = typer.Option("", "--head-title", help="Card head title"),
    body_sub_title: str = typer.Option("", "--sub-title", help="Card sub title"),
    body_content: str = typer.Option("", "--content", help="Card body content"),
    signature: str = typer.Option("", "--signature", help="Card signature"),
    card_link: str = typer.Option("", "--card-link", help="Card link URL"),
    pc_card_link: str = typer.Option("", "--pc-card-link", help="PC card link URL"),
    is_dynamic: bool = typer.Option(False, "--dynamic", help="Enable dynamic card updates"),
    staff_id: str = typer.Option("", "--staff-id", help="Staff ID"),
    head_icon_url: str = typer.Option("", "--head-icon", help="Head icon URL"),
):
    client = get_client()
    result = client.send_app_card(
        chat_id=chat_id, body_title=body_title,
        head_title=head_title, body_sub_title=body_sub_title,
        body_content=body_content, signature=signature,
        card_link=card_link, pc_card_link=pc_card_link,
        is_dynamic=is_dynamic, staff_id=staff_id, head_icon_url=head_icon_url,
    )
    output_result(result, fields=["message_id", "msg_type", "operation"], title="Send App Card Result")


@app.command("update-dynamic-card")
def update_dynamic_card(
    msg_id: str = typer.Argument(help="Message ID of the dynamic card"),
    is_last_update: bool = typer.Option(False, "--last", help="Mark as last update"),
):
    client = get_client()
    result = client.update_dynamic_card(msg_id=msg_id, is_last_update=is_last_update)
    output_result(result, fields=["message_id", "operation"], title="Update Dynamic Card Result")


@app.command("revoke")
def revoke_message(
    message_ids: List[str] = typer.Argument(help="Message IDs to revoke"),
    chat_type: str = typer.Option("bot", "--chat-type", help="bot, account, or private"),
    sender_id: str = typer.Option("", "--sender-id", help="Sender staff ID"),
):
    client = get_client()
    result = client.revoke_message(message_ids=message_ids, chat_type=chat_type, sender_id=sender_id)
    output_result(result, fields=["message_id", "operation"], title="Revoke Message Result")


@app.command("query-groups")
def query_groups(
    page_offset: int = typer.Option(1, "--page", "-p", help="Page offset"),
    page_size: int = typer.Option(100, "--size", "-s", help="Page size"),
):
    client = get_client()
    result = client.query_groups(page_offset=page_offset, page_size=page_size)
    if result.success:
        output_result(result, fields=["total_group_ids", "operation"], title="Query Groups Result")
        if result.group_ids:
            output_list(result.group_ids, columns=["Group ID"], title="Groups", row_mapper=lambda gid: [gid])
    else:
        output_result(result)