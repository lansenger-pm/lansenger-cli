"""Tests for the `lansenger media` command group."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lansenger_cli.main import app
from lansenger_sdk import LansengerFileError

runner = CliRunner()


def test_download_to_file_failure_is_reported_not_raised():
    """download_media_to_file 的文档契约是失败抛异常；CLI 必须转成友好错误 + 退出码 1。"""
    with patch("lansenger_cli.commands.media.get_client") as gc:
        client = MagicMock()
        client.download_media_to_file.side_effect = LansengerFileError(
            "Download failed: Download returned an API error instead of a file (errCode=10003)"
        )
        gc.return_value = client
        result = runner.invoke(app, ["media", "download-to-file", "m-1"])
    assert result.exit_code == 1
    assert "Download failed" in result.output
    assert "Traceback" not in result.output


def test_download_to_file_success_prints_path():
    with patch("lansenger_cli.commands.media.get_client") as gc:
        client = MagicMock()
        client.download_media_to_file.return_value = "/tmp/x.bin"
        gc.return_value = client
        result = runner.invoke(app, ["media", "download-to-file", "m-1"])
    assert result.exit_code == 0, result.output
    assert "/tmp/x.bin" in result.output
