"""Unit tests for CLI --loglevel argument parsing.

Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6
"""

import argparse
import logging

import pytest


def _make_parser():
    """Create a minimal parser mirroring the --loglevel argument from main()."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--loglevel",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    return parser


def test_loglevel_defaults_to_info():
    """--loglevel defaults to INFO when not provided."""
    parser = _make_parser()
    args = parser.parse_args([])
    assert args.loglevel == "INFO"
    assert getattr(logging, args.loglevel) == logging.INFO


def test_loglevel_lowercase_debug_accepted():
    """--loglevel debug (lowercase) is accepted and resolves to logging.DEBUG."""
    parser = _make_parser()
    args = parser.parse_args(["--loglevel", "debug"])
    assert args.loglevel == "DEBUG"
    assert getattr(logging, args.loglevel) == logging.DEBUG


def test_loglevel_trace_rejected():
    """--loglevel TRACE is rejected by argparse."""
    parser = _make_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--loglevel", "TRACE"])


def test_loglevel_numeric_rejected():
    """--loglevel 3 (numeric) is rejected by argparse."""
    parser = _make_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--loglevel", "3"])
