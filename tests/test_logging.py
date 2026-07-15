import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lansenger_cli.utils import set_verbose, is_verbose


def test_set_verbose_true():
    """set_verbose(True) enables verbose mode and sets DEBUG level on lansenger_sdk logger."""
    set_verbose(True)
    assert is_verbose() is True
    root = logging.getLogger("lansenger_sdk")
    assert root.level == logging.DEBUG
    assert len(root.handlers) >= 1
    set_verbose(False)


def test_set_verbose_false():
    """set_verbose(False) disables verbose mode and resets logger to WARNING."""
    set_verbose(True)
    set_verbose(False)
    assert is_verbose() is False
    root = logging.getLogger("lansenger_sdk")
    assert root.level == logging.WARNING
    set_verbose(False)


def test_set_verbose_twice_no_duplicate_handlers():
    """Calling set_verbose(True) twice does not add duplicate handlers."""
    set_verbose(False)
    set_verbose(True)
    root = logging.getLogger("lansenger_sdk")
    handler_count = len(root.handlers)
    set_verbose(True)
    assert len(root.handlers) == handler_count
    set_verbose(False)
