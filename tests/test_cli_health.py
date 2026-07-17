import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_cli.utils import set_json_output, set_active_profile


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset global state between tests to avoid cross-test interference."""
    set_json_output(False)
    set_active_profile("default")


def test_health_check_pass():
    """`lansenger health check` reports OK when connection is healthy."""
    mock_client = MagicMock()
    mock_client.health_check.return_value = True

    with patch("lansenger_cli.commands.health.get_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(app, ["health", "check"])

    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_health_check_fail():
    """`lansenger health check` reports FAIL and exits non-zero on failure."""
    mock_client = MagicMock()
    mock_client.health_check.return_value = False

    with patch("lansenger_cli.commands.health.get_client", return_value=mock_client):
        runner = CliRunner()
        result = runner.invoke(app, ["health", "check"])

    assert result.exit_code == 1
    assert "FAIL" in result.stdout
