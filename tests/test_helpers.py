"""Tests for pure utility functions."""

from lxmf_group.helpers import CommandDict, qr_unicode


def test_qr_unicode_returns_string():
    result = qr_unicode("test")
    assert isinstance(result, str)
    assert len(result) > 0


def test_qr_unicode_empty_on_failure():
    # qr_unicode should not raise, just return ""
    result = qr_unicode("")
    assert isinstance(result, str)
