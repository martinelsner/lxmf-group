"""Unit tests for setup_logging() handler configuration."""

import logging

import pytest

from lxmf_group.helpers import setup_logging


@pytest.fixture(autouse=True)
def _clean_handlers():
    """Remove all handlers from the root logger after each test."""
    yield
    logging.getLogger().handlers.clear()


def test_console_only_attaches_one_stream_handler():
    """Calling setup_logging attaches exactly one StreamHandler."""
    setup_logging(logging.DEBUG)
    root = logging.getLogger()

    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], logging.StreamHandler)
