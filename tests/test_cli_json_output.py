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


def _invoke_json(group: str, method: str, result):
    with patch(f"lansenger_cli.commands.{group}.get_client") as gc:
        client = MagicMock()
        getattr(client, method).return_value = result
        gc.return_value = client
        return runner.invoke(app, ["--json", group, *ARGS[group]])


ARGS = {"group": ["members", "g-1"], "message": ["query-groups"]}


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
