"""Tests for the `lansenger personal-todo` command group."""

import base64
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_sdk.models import (
    PersonalTodoListResult,
    PersonalTodoResourceResult,
    PersonalTodoSaveResult,
    PersonalTodoUrlResult,
)

runner = CliRunner()


def test_personal_todo_group_registered():
    result = runner.invoke(app, ["personal-todo", "--help"])
    assert result.exit_code == 0
    for command in ("save", "update", "list", "upload-resource", "download-url", "upload-url"):
        assert command in result.output


def test_save_personal_todo_parses_json_lists():
    with patch("lansenger_cli.commands.personal_todo.get_client") as gc:
        client = MagicMock()
        client.save_personal_todo.return_value = PersonalTodoSaveResult(success=True, todo_code="TASK1")
        gc.return_value = client
        result = runner.invoke(app, [
            "personal-todo", "save", "完成方案", "staff1", "org1", "app1",
            "--start-time", "100", "--due-time", "200", "--priority", "2",
            "--executors", '[{"staffId":"staff1","opt":1}]',
            "--resources", '[{"fileName":"a.pdf","resourceId":"r1"}]',
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.save_personal_todo.call_args.kwargs
    assert kwargs["subject"] == "完成方案"
    assert kwargs["priority"] == 2
    assert kwargs["executors"] == [{"staffId": "staff1", "opt": 1}]
    assert kwargs["resources"] == [{"fileName": "a.pdf", "resourceId": "r1"}]


def test_update_personal_todo_parses_fields():
    with patch("lansenger_cli.commands.personal_todo.get_client") as gc:
        client = MagicMock()
        client.update_personal_todo.return_value = PersonalTodoSaveResult(success=True, todo_code="TASK1")
        gc.return_value = client
        result = runner.invoke(app, [
            "personal-todo", "update", "TASK1", "org1",
            "--update-fields", "subject,dueTime",
            "--subject", "新主题", "--due-time", "300",
            "--create-user-id", "staff1", "--appid", "app1",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.update_personal_todo.call_args.kwargs
    assert kwargs["update_fields"] == ["subject", "dueTime"]
    assert kwargs["subject"] == "新主题"
    assert kwargs["due_time"] == 300
    assert kwargs["create_user_id"] == "staff1"
    assert kwargs["appid"] == "app1"


def test_list_personal_todos_renders_items():
    with patch("lansenger_cli.commands.personal_todo.get_client") as gc:
        client = MagicMock()
        client.fetch_personal_todo_list.return_value = PersonalTodoListResult(
            success=True,
            total=1,
            page_no=1,
            page_size=10,
            items=[{"taskCode": "TASK1", "summarySubject": "方案", "status": 0}],
        )
        gc.return_value = client
        result = runner.invoke(app, [
            "personal-todo", "list", "org1", "staff1", "--status", "0",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.fetch_personal_todo_list.call_args.kwargs
    assert kwargs["org_id"] == "org1" and kwargs["staff_id"] == "staff1"
    assert kwargs["status"] == 0
    assert "TASK1" in result.output
    assert "方案" in result.output


def test_upload_resource_reads_local_file(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"hello")
    with patch("lansenger_cli.commands.personal_todo.get_client") as gc:
        client = MagicMock()
        client.upload_personal_todo_resource.return_value = PersonalTodoResourceResult(
            success=True, resource_id="res1", file_name="a.txt", size=5,
        )
        gc.return_value = client
        result = runner.invoke(app, [
            "personal-todo", "upload-resource", "app1", "a.txt", "text/plain", "org1",
            "--file", str(file_path),
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.upload_personal_todo_resource.call_args.kwargs
    assert kwargs["size"] == 5
    assert kwargs["file_data"] == base64.b64encode(b"hello").decode("ascii")
    assert "res1" in result.output


def test_resource_urls_pass_parameters():
    with patch("lansenger_cli.commands.personal_todo.get_client") as gc:
        client = MagicMock()
        client.fetch_personal_todo_resource_download_url.return_value = PersonalTodoUrlResult(
            success=True, url="https://example.com/download",
        )
        client.fetch_personal_todo_resource_upload_url.return_value = PersonalTodoUrlResult(
            success=True, url="https://example.com/upload",
        )
        gc.return_value = client

        download = runner.invoke(app, [
            "personal-todo", "download-url", "res1", "org1",
        ])
        upload = runner.invoke(app, [
            "personal-todo", "upload-url", "a.txt", "md5", "10", "org1",
        ])

    assert download.exit_code == 0, download.output
    assert upload.exit_code == 0, upload.output
    client.fetch_personal_todo_resource_download_url.assert_called_once_with(
        resource_id="res1", org_id="org1", file_name="", user_token="",
    )
    client.fetch_personal_todo_resource_upload_url.assert_called_once_with(
        file_name="a.txt", md5="md5", size=10, org_id="org1", user_token="",
    )
