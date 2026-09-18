"""Tests for the `lansenger questionnaire` command group."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_sdk.models import (
    QuestionnaireOpResult,
    QuestionnairePageResult,
    QuestionnaireSaveResult,
)

runner = CliRunner()


def test_questionnaire_group_registered():
    result = runner.invoke(app, ["questionnaire", "--help"])
    assert result.exit_code == 0
    for name in ("save", "publish", "delete", "accounts", "answers", "upload-url"):
        assert name in result.output


def test_save_passes_params():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        client = MagicMock()
        client.save_questionnaire.return_value = QuestionnaireSaveResult(success=True, questionnaire_code="QN1")
        gc.return_value = client
        result = runner.invoke(app, [
            "questionnaire", "save", "满意度调查", "ACC001",
            "--welcome", "欢迎", "--create-user-id", "U1",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.save_questionnaire.call_args.kwargs
    assert kwargs["title"] == "满意度调查"
    assert kwargs["account_code"] == "ACC001"
    assert kwargs["welcome_speech"] == "欢迎"
    assert kwargs["create_user_id"] == "U1"


def test_save_questions_parses_json():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        client = MagicMock()
        client.save_questionnaire_questions.return_value = MagicMock(success=True, saved_count=1)
        gc.return_value = client
        result = runner.invoke(app, [
            "questionnaire", "save-questions", "QN1",
            "--questions", '[{"questionName":"Q1","questionType":"radio","requiredFlag":1}]',
        ])
    assert result.exit_code == 0, result.output
    args = client.save_questionnaire_questions.call_args.args
    assert args[0] == "QN1"
    assert args[1][0]["questionType"] == "radio"


def test_publish_passes_parsed_lists():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        client = MagicMock()
        client.publish_questionnaire.return_value = QuestionnaireOpResult(success=True, done=True)
        gc.return_value = client
        result = runner.invoke(app, [
            "questionnaire", "publish", "QN1",
            "--scope", "2", "--staff-ids", "U1, U2", "--message-flag", "1",
        ])
    assert result.exit_code == 0, result.output
    kwargs = client.publish_questionnaire.call_args.kwargs
    assert kwargs["scope_type"] == 2
    assert kwargs["staff_ids"] == ["U1", "U2"]
    assert kwargs["message_flag"] == 1


def test_delete_requires_yes():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        result = runner.invoke(app, ["questionnaire", "delete", "QN1"])
    assert result.exit_code == 10
    gc.assert_not_called()

    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        client = MagicMock()
        client.delete_questionnaire.return_value = QuestionnaireOpResult(success=True, done=True)
        gc.return_value = client
        result = runner.invoke(app, ["questionnaire", "delete", "QN1", "--yes"])
    assert result.exit_code == 0
    client.delete_questionnaire.assert_called_once()


def test_delete_dry_run():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        result = runner.invoke(app, ["questionnaire", "delete", "QN1", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    gc.assert_not_called()


def test_created_list_renders_rows():
    with patch("lansenger_cli.commands.questionnaire.get_client") as gc:
        client = MagicMock()
        client.fetch_created_questionnaires.return_value = QuestionnairePageResult(
            success=True, total=1, page_no=1, page_size=10, has_more=False,
            items=[{"code": "QN1", "title": "满意度", "status": 2, "answerUserCount": 5}],
        )
        gc.return_value = client
        result = runner.invoke(app, ["questionnaire", "created-list", "ACC001"])
    assert result.exit_code == 0, result.output
    assert "QN1" in result.output and "满意度" in result.output
