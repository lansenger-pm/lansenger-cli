import json
from typing import Optional

import typer

from lansenger_cli.utils import (
    confirm_high_risk,
    get_client,
    is_json_output,
    output_list,
    output_result,
)

app = typer.Typer(help="Manage questionnaires (问卷系统)")

_PAGE_FIELDS = ["total", "page_no", "page_size", "has_more"]


def _opt_int(value: Optional[int]) -> Optional[int]:
    return value


def _print_page_items(items, columns, row_mapper=None, title="Result"):
    if not items or is_json_output():
        return

    def safe_mapper(item):
        mapper = row_mapper or (lambda i: [i.get(c, "") for c in columns])
        return [str(v) if v is not None else "" for v in mapper(item)]

    output_list(items, columns=columns, title=title, row_mapper=safe_mapper)


@app.command("save")
def save_questionnaire(
    title: str = typer.Argument(help="Questionnaire title (max 100 chars)"),
    account_code: str = typer.Argument(help="Official account CODE (see `questionnaire accounts`)"),
    code: str = typer.Option("", "--code", help="Existing questionnaire code (update when given)"),
    welcome: str = typer.Option("", "--welcome", help="Welcome speech (max 2000 chars)"),
    bye: str = typer.Option("", "--bye", help="Bye speech (max 100 chars)"),
    cover: str = typer.Option("", "--cover", help="Cover resource ID"),
    resource_ids: str = typer.Option("", "--resource-ids", help="Comma-joined resource id string"),
    create_mobile: str = typer.Option("", "--create-mobile", help="Operator mobile (omit when --as/--user-token is set)"),
    create_user_id: str = typer.Option("", "--create-user-id", help="Creator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Create a questionnaire (or update when --code is given)"""
    client = get_client()
    result = client.save_questionnaire(
        title=title, account_code=account_code, code=code, welcome_speech=welcome,
        bye_speech=bye, cover_resource_id=cover, resource_ids=resource_ids,
        create_mobile=create_mobile, create_user_id=create_user_id, user_token=user_token,
    )
    output_result(result, fields=["questionnaire_code"], title="Save Questionnaire Result")


@app.command("save-questions")
def save_questions(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    questions: str = typer.Option(..., "--questions", help='JSON list of questions (camelCase): \'[{"questionName":"Q1","questionType":"radio","requiredFlag":1,"questionOptionList":[{"optionName":"A"}]}]\''),
    create_user_id: str = typer.Option("", "--create-user-id", help="Creator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Batch-save questions (new or update; 16 question types)"""
    client = get_client()
    result = client.save_questionnaire_questions(
        questionnaire_code, json.loads(questions),
        create_user_id=create_user_id, user_token=user_token,
    )
    output_result(result, fields=["saved_count"], title="Save Questions Result")


@app.command("delete-question")
def delete_question(
    question_code: str = typer.Argument(help="Question code"),
    create_user_id: str = typer.Option("", "--create-user-id", help="Creator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm question deletion before executing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without deleting"),
):
    """Delete a question by code"""
    confirm_high_risk("delete", f"question {question_code}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    client = get_client()
    result = client.delete_questionnaire_question(
        question_code, create_user_id=create_user_id, user_token=user_token,
    )
    output_result(result, fields=["deleted"], title="Delete Question Result")


@app.command("publish")
def publish(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    scope: int = typer.Option(1, "--scope", help="Publish scope: 1=internal, 2=public"),
    staff_ids: str = typer.Option("", "--staff-ids", help="Comma-separated target staff openIds (internal scope)"),
    phones: str = typer.Option("", "--phones", help="Comma-separated target mobiles (internal scope)"),
    answer_limit: int = typer.Option(1, "--answer-limit", help="Answer limit: 1=once, -1=unlimited"),
    message_flag: int = typer.Option(0, "--message-flag", help="Official-account message: 1=on, 0=off"),
    page_flag: int = typer.Option(0, "--page-flag", help="One question per page: 1=on, 0=off"),
    share_flag: int = typer.Option(0, "--share-flag", help="Allow sharing: 1=on, 0=off"),
    view_stats_flag: int = typer.Option(1, "--view-stats-flag", help="Allow viewing stats: 1=on, 0=off"),
    anonym_flag: int = typer.Option(0, "--anonym-flag", help="Allow anonymous answers: 1=on, 0=off"),
    publish_user_id: str = typer.Option("", "--publish-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Publish a questionnaire"""
    client = get_client()
    result = client.publish_questionnaire(
        questionnaire_code, scope_type=scope,
        staff_ids=[s.strip() for s in staff_ids.split(",") if s.strip()] or None,
        phones=[p.strip() for p in phones.split(",") if p.strip()] or None,
        answer_limit=answer_limit, message_flag=message_flag, page_flag=page_flag,
        share_flag=share_flag, view_stats_flag=view_stats_flag, anonym_flag=anonym_flag,
        publish_user_id=publish_user_id, user_token=user_token,
    )
    output_result(result, fields=["done"], title="Publish Questionnaire Result")


@app.command("withdraw")
def withdraw(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Withdraw a published questionnaire back to draft"""
    client = get_client()
    result = client.withdraw_questionnaire(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(result, fields=["done"], title="Withdraw Result")


@app.command("finish")
def finish(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """End an ongoing questionnaire (no more answers)"""
    client = get_client()
    result = client.finish_questionnaire(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(result, fields=["done"], title="Finish Result")


@app.command("delete")
def delete_questionnaire(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm questionnaire deletion before executing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate inputs without deleting"),
):
    """Delete a questionnaire"""
    confirm_high_risk("delete", f"questionnaire {questionnaire_code}", yes=yes, dry_run=dry_run)
    if dry_run:
        return
    client = get_client()
    result = client.delete_questionnaire(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(result, fields=["done"], title="Delete Questionnaire Result")


@app.command("detail")
def detail(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch full questionnaire detail incl. questions (needs admin permission)"""
    client = get_client()
    result = client.fetch_questionnaire_detail(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(
        result,
        fields=["code", "title", "status", "question_count", "answer_user_count", "account_code", "questions"],
        title="Questionnaire Detail",
    )


@app.command("brief")
def brief(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch questionnaire detail without admin check (no questions)"""
    client = get_client()
    result = client.fetch_questionnaire_brief(questionnaire_code, user_token=user_token)
    output_result(
        result,
        fields=["code", "title", "status", "question_count", "answer_user_count", "account_code"],
        title="Questionnaire Brief",
    )


@app.command("answer-url")
def answer_url(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch the answer-page URL"""
    client = get_client()
    result = client.fetch_questionnaire_answer_url(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(result, fields=["url"], title="Answer URL")


@app.command("copy")
def copy_questionnaire(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    operate_user_id: str = typer.Option("", "--operate-user-id", help="Operator staff ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Copy a questionnaire into a new draft"""
    client = get_client()
    result = client.copy_questionnaire(questionnaire_code, operate_user_id=operate_user_id, user_token=user_token)
    output_result(result, fields=["new_code"], title="Copy Questionnaire Result")


@app.command("query-codes")
def query_codes(
    codes: str = typer.Option(..., "--codes", help="Comma-separated questionnaire codes"),
    include_deleted: int = typer.Option(0, "--include-deleted", help="0=exclude deleted, 1=include"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Batch-fetch questionnaire basic info by codes"""
    client = get_client()
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    result = client.fetch_questionnaires_by_codes(code_list, include_deleted=include_deleted, user_token=user_token)
    output_result(result, fields=["total"], title="Questionnaire Query Result")
    _print_page_items(
        result.items, ["code", "title", "status", "questionCount"],
        row_mapper=lambda i: [i.get("code", ""), i.get("title", ""), i.get("status", ""), i.get("questionCount", "")],
        title="Questionnaires",
    )


@app.command("accounts")
def accounts(
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch office accounts the user can manage (accountCode source)"""
    client = get_client()
    result = client.fetch_questionnaire_office_accounts(user_id=user_id, user_token=user_token)
    output_result(result, fields=["total"], title="Questionnaire Office Accounts")
    _print_page_items(
        result.accounts, ["code", "roleName", "cmcName"],
        row_mapper=lambda a: [a.get("code", ""), a.get("roleName", ""), a.get("cmcName", "")],
        title="Office Accounts",
    )
@app.command("created-list")
def created_list(
    account_code: str = typer.Argument(help="Official account CODE"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    status: Optional[int] = typer.Option(None, "--status", help="1=draft, 2=ongoing, 3=withdrawn, 4=finished"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page questionnaires created under an office account"""
    client = get_client()
    result = client.fetch_created_questionnaires(
        account_code, page_no=page, page_size=size, status=status,
        user_id=user_id, user_token=user_token,
    )
    output_result(result, fields=_PAGE_FIELDS, title="Created Questionnaires")
    _print_page_items(
        result.items, ["code", "title", "status", "answerUserCount"],
        row_mapper=lambda i: [i.get("code", ""), i.get("title", ""), i.get("status", ""), i.get("answerUserCount", "")],
        title="Questionnaires",
    )


@app.command("my-created")
def my_created(
    org_id: str = typer.Argument(help="Organization ID"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    title: str = typer.Option("", "--title", help="Filter by title"),
    status: Optional[int] = typer.Option(None, "--status", help="1=draft, 2=ongoing, 3=withdrawn, 4=finished"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page all questionnaires I created (personal + official)"""
    client = get_client()
    result = client.fetch_my_created_questionnaires(
        org_id, page_no=page, page_size=size, title=title, status=status,
        user_id=user_id, user_token=user_token,
    )
    output_result(result, fields=_PAGE_FIELDS, title="My Created Questionnaires")
    _print_page_items(
        result.items, ["code", "title", "status", "accountName"],
        row_mapper=lambda i: [i.get("code", ""), i.get("title", ""), i.get("status", ""), i.get("accountName", "")],
        title="Questionnaires",
    )


@app.command("participated")
def participated(
    org_id: str = typer.Argument(help="Organization ID"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    status: Optional[int] = typer.Option(None, "--status", help="2=ongoing, 4=finished"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page questionnaires the user answered"""
    client = get_client()
    result = client.fetch_participated_questionnaires(
        org_id, page_no=page, page_size=size, status=status,
        user_id=user_id, user_token=user_token,
    )
    output_result(result, fields=_PAGE_FIELDS, title="Participated Questionnaires")
    _print_page_items(
        result.items, ["code", "title", "status", "accountName"],
        row_mapper=lambda i: [i.get("code", ""), i.get("title", ""), i.get("status", ""), i.get("accountName", "")],
        title="Questionnaires",
    )


@app.command("answers")
def answers(
    account_code: str = typer.Argument(help="Official account CODE"),
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page answer records of a questionnaire"""
    client = get_client()
    result = client.fetch_answer_records(
        account_code, questionnaire_code, page_no=page, page_size=size,
        user_id=user_id, user_token=user_token,
    )
    output_result(result, fields=_PAGE_FIELDS, title="Answer Records")
    _print_page_items(
        result.items, ["code", "answerUserName", "answerStatus", "answerCommitTime"],
        row_mapper=lambda i: [i.get("code", ""), i.get("answerUserName", ""), i.get("answerStatus", ""), i.get("answerCommitTime", "")],
        title="Answer Records",
    )


@app.command("answer-detail")
def answer_detail(
    account_code: str = typer.Argument(help="Official account CODE"),
    answer_code: str = typer.Argument(help="Answer record code"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch one answer record's full detail (questionnaire + questions + answers)"""
    client = get_client()
    result = client.fetch_questionnaire_answer_detail(
        account_code, answer_code, user_id=user_id, user_token=user_token,
    )
    output_result(
        result,
        fields=["answer_code", "answer_user_name", "answer_status", "answer_commit_time", "questionnaire", "answers"],
        title="Answer Detail",
    )


@app.command("last-answer-detail")
def last_answer_detail(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    answer_record_code: str = typer.Option("", "--answer-record-code", help="Specific answer record code"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch the user's last answer detail for a questionnaire"""
    client = get_client()
    result = client.fetch_questionnaire_last_answer_detail(
        questionnaire_code, answer_record_code=answer_record_code,
        user_id=user_id, user_token=user_token,
    )
    output_result(
        result,
        fields=["answer_code", "answer_user_name", "answer_status", "answer_commit_time", "answers"],
        title="Last Answer Detail",
    )


@app.command("answer-data")
def answer_data(
    account_code: str = typer.Argument(help="Official account CODE"),
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    page: int = typer.Option(1, "--page", help="Page number"),
    size: int = typer.Option(10, "--size", help="Page size"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Page answer data for export (JSON structure)"""
    client = get_client()
    result = client.fetch_answer_data(
        account_code, questionnaire_code, page_no=page, page_size=size,
        user_id=user_id, user_token=user_token,
    )
    output_result(result, fields=_PAGE_FIELDS, title="Answer Data")
    _print_page_items(
        result.items, ["code", "answerUserName", "answerCommitTime"],
        row_mapper=lambda i: [i.get("code", ""), i.get("answerUserName", ""), i.get("answerCommitTime", "")],
        title="Answer Data",
    )


@app.command("last-answer-record")
def last_answer_record(
    questionnaire_code: str = typer.Argument(help="Questionnaire code"),
    answer_record_code: str = typer.Option("", "--answer-record-code", help="Specific answer record code"),
    user_id: str = typer.Option("", "--user-id", help="User ID (omit when --as/--user-token is set)"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch the user's last answer record (main table only)"""
    client = get_client()
    result = client.fetch_questionnaire_last_answer_record(
        questionnaire_code, answer_record_code=answer_record_code,
        user_id=user_id, user_token=user_token,
    )
    output_result(
        result,
        fields=["record_code", "answer_user_name", "answer_status", "answer_commit_time", "stats_status"],
        title="Last Answer Record",
    )


@app.command("upload-url")
def upload_url(
    file_name: str = typer.Argument(help="File name with extension"),
    md5: str = typer.Argument(help="File MD5 hex digest"),
    size: int = typer.Argument(help="File size in bytes"),
    user_token: str = typer.Option("", "--user-token", help="User token"),
):
    """Fetch a presigned upload URL (then PUT the file with a Content-MD5 header)"""
    client = get_client()
    result = client.fetch_questionnaire_upload_url(file_name, md5, size, user_token=user_token)
    output_result(result, fields=["url"], title="Upload URL")
