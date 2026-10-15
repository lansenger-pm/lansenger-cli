"""Regression tests: ``--json`` stdout must stay exactly one machine-readable JSON document.

历史缺陷：``output_list()`` 在 JSON 模式下用 rich 打印 Python repr 列表，
使 ``group members --json`` 之类命令的 stdout 变成「JSON 对象 + repr 列表」两段，
下游 ``json.loads(stdout)`` 直接抛 JSONDecodeError。列表本身已经在 result JSON 里，
因此 JSON 模式下不应再单独输出。
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app

runner = CliRunner()


CLI_NAMES = {"personal_app": "personal-app"}  # 子命令注册名（kebab）与模块名（下划线）不同者在此映射


def _invoke_json(group: str, method: str, result):
    with patch(f"lansenger_cli.commands.{group}.get_client") as gc:
        client = MagicMock()
        getattr(client, method).return_value = result
        gc.return_value = client
        return runner.invoke(app, ["--json", CLI_NAMES.get(group, group), *ARGS[group]])


ARGS = {"group": ["members", "g-1"], "message": ["query-groups"], "personal_app": ["list"], "calendar": ["list-schedules", "cal-1", "0", "9"]}


def test_group_members_json_stdout_is_a_single_document():
    result = MagicMock()
    result.success = True
    result.total_members = 2
    result.members = [
        {"staffId": "u1", "name": "A", "role": "member"},
        {"staffId": "u2", "name": "B", "role": "member"},
    ]
    result.to_dict.return_value = {"success": True, "total_members": 2, "members": result.members}
    out = _invoke_json("group", "fetch_group_members", result)
    assert out.exit_code == 0, out.output
    payload = json.loads(out.stdout)
    assert payload["total_members"] == 2
    assert [m["staffId"] for m in payload["members"]] == ["u1", "u2"]


def test_query_groups_json_stdout_is_a_single_document():
    result = MagicMock()
    result.success = True
    result.total_group_ids = 1
    result.group_ids = ["g-1"]
    result.to_dict.return_value = {"success": True, "total_group_ids": 1, "group_ids": ["g-1"]}
    out = _invoke_json("message", "query_groups", result)
    assert out.exit_code == 0, out.output
    payload = json.loads(out.stdout)
    assert payload["group_ids"] == ["g-1"]


def test_personal_app_list_json_stdout_is_a_single_document():
    """output_list 是该命令成功路径的唯一列表输出的形态：JSON 模式必须由 output_result 出一份 JSON。"""
    result = MagicMock()
    result.success = True
    result.app_list = [
        {"appId": "123-456", "appName": "A", "description": ""},
    ]
    result.to_dict.return_value = {"success": True, "app_list": result.app_list}
    out = _invoke_json("personal_app", "fetch_personal_app_list", result)
    assert out.exit_code == 0, out.output
    payload = json.loads(out.stdout)
    assert payload["app_list"][0]["appId"] == "123-456"


def test_calendar_list_schedules_json_stdout_is_a_single_document():
    result = MagicMock()
    result.success = True
    result.schedule_list = [
        {"scheduleId": "s-1", "summary": "demo"},
    ]
    result.to_dict.return_value = {"success": True, "schedule_list": result.schedule_list}
    out = _invoke_json("calendar", "fetch_schedule_list", result)
    assert out.exit_code == 0, out.output
    payload = json.loads(out.stdout)
    assert payload["schedule_list"][0]["scheduleId"] == "s-1"
