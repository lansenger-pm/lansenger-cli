import json
from typing import Optional

import typer

from lansenger_cli.utils import get_client, is_json_output, output_list, output_result

app = typer.Typer(help="Send notices via official accounts (通知系统)")


@app.command("send")
def send_notice(
    title: str = typer.Argument(help="Notice title"),
    account_code: str = typer.Argument(help="Official account CODE (see `notice accounts`)"),
    content: str = typer.Option("", "--content", "-c", help="Text content (required when --content-type is 1)"),
    notice_link: str = typer.Option("", "--link", help="Link URL (required when --content-type is 2)"),
    content_type: int = typer.Option(1, "--content-type", "-t", help="Content type: 1=text, 2=link"),
    user_type: int = typer.Option(1, "--user-type", "-u", help="Targeting type: 1=phone, 2=staffId/department"),
    release_phones: str = typer.Option("", "--release-phones", help="Comma-separated receiver phones (user-type=1, max 10)"),
    cc_phones: str = typer.Option("", "--cc-phones", help="Comma-separated cc phones (user-type=1, max 10)"),
    release_range: str = typer.Option("", "--release-range", help='JSON list of range items (user-type=2, max 200): \'[{"objId":"dept-1","objName":"研发部","objType":2}]\' (objType: 1=staff, 2=department)'),
    cc_staff_ids: str = typer.Option("", "--cc-staff-ids", help="Comma-separated cc staff IDs (user-type=2, max 200)"),
    create_mobile: str = typer.Option("", "--create-mobile", help="Operator mobile (user-type=1; omit when --as/--user-token is set)"),
    create_user_id: str = typer.Option("", "--create-user-id", help="Creator staff ID (user-type=2; omit when --as/--user-token is set)"),
    location: str = typer.Option("", "--location", help="Notice address"),
    resources: str = typer.Option("", "--resources", help='JSON list of attachments: \'[{"fileName":"a.pdf","resourceId":"res-1","fileType":"application/pdf","fileSize":1024}]\''),
    extend_id: str = typer.Option("", "--extend-id", help="Caller-side correlation ID"),
    confirm_flag: Optional[int] = typer.Option(None, "--confirm-flag", help="Require read confirmation: 1=yes, 0=no"),
    forward_flag: Optional[int] = typer.Option(None, "--forward-flag", help="Allow forwarding: 1=yes, 0=no"),
    reply_flag: Optional[int] = typer.Option(None, "--reply-flag", help="Allow reply: 1=yes, 0=no"),
    anonymous_flag: Optional[int] = typer.Option(None, "--anonymous-flag", help="Allow anonymous reply: 1=yes, 0=no"),
    remind_status: Optional[int] = typer.Option(None, "--remind-status", help="Enable reminding: 1=yes, 0=no"),
    remind_msg_type: str = typer.Option("", "--remind-msg-type", help="Remind channels, comma-separated: mobile,sms,app"),
    at_once_flag: Optional[int] = typer.Option(None, "--at-once", help="Remind immediately: 1=yes, 0=no"),
    remind_after_type: str = typer.Option("", "--remind-after", help="Follow-up remind type: never, unOperate, count"),
    remind_max_count: Optional[int] = typer.Option(None, "--remind-max-count", help="Max remind count (remind-after=count)"),
    remind_interval_time: Optional[int] = typer.Option(None, "--remind-interval", help="Remind interval value"),
    remind_interval_time_duration: str = typer.Option("", "--remind-interval-unit", help="Interval unit: minutes, hour, day"),
    remind_range_type: str = typer.Option("", "--remind-range", help="Remind range type: all, receiver, partialRemind, notReminder"),
    remind_exclude_ids: str = typer.Option("", "--remind-exclude", help="Comma-separated staff IDs excluded from reminding"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Send a notice via an official account"""
    client = get_client()
    phones = [p.strip() for p in release_phones.split(",") if p.strip()] if release_phones else None
    cc_phone_list = [p.strip() for p in cc_phones.split(",") if p.strip()] if cc_phones else None
    range_items = json.loads(release_range) if release_range else None
    cc_ids = [s.strip() for s in cc_staff_ids.split(",") if s.strip()] if cc_staff_ids else None
    resource_items = json.loads(resources) if resources else None
    exclude_ids = [s.strip() for s in remind_exclude_ids.split(",") if s.strip()] if remind_exclude_ids else None
    result = client.send_notice(
        title=title,
        content_type=content_type,
        account_code=account_code,
        user_type=user_type,
        content=content,
        notice_link=notice_link,
        notice_location=location,
        release_phones=phones,
        cc_phones=cc_phone_list,
        release_range=range_items,
        cc_staff_ids=cc_ids,
        create_mobile=create_mobile,
        create_user_id=create_user_id,
        resource_list=resource_items,
        extend_id=extend_id,
        confirm_flag=confirm_flag,
        forward_flag=forward_flag,
        reply_flag=reply_flag,
        anonymous_flag=anonymous_flag,
        remind_status=remind_status,
        remind_msg_type=remind_msg_type,
        at_once_flag=at_once_flag,
        remind_after_type=remind_after_type,
        remind_max_count=remind_max_count,
        remind_interval_time=remind_interval_time,
        remind_interval_time_duration=remind_interval_time_duration,
        remind_range_type=remind_range_type,
        remind_range_staff_ids=exclude_ids,
        user_token=user_token,
    )
    output_result(
        result,
        fields=["notice_code", "title", "notice_status", "confirm_status", "publish_user_name"],
        title="Send Notice Result",
    )


@app.command("accounts")
def fetch_notice_accounts(
    org_id: str = typer.Option("", "--org-id", help="Organization ID"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """List official accounts (fetch accountCode for sending)"""
    client = get_client()
    result = client.fetch_notice_accounts(org_id=org_id, user_token=user_token)
    output_result(result, fields=["total"], title="Notice Accounts")
    if result.accounts and not is_json_output():
        output_list(
            result.accounts,
            columns=["roleName", "officialNumberId", "code"],
            title="Official Accounts",
            row_mapper=lambda a: [a.get(c, "") for c in ("roleName", "officialNumberId", "code")],
        )
