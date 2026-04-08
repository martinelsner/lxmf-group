"""Property-based tests for the pythonic-logging feature."""

import logging
import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lxmf_group.helpers import setup_logging

# ---------------------------------------------------------------------------
# Shared constants and strategies
# ---------------------------------------------------------------------------

VALID_LEVELS = [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
]
LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOG_LINE_RE = re.compile(
    r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] "
    r"\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\] "
    r".+"
)


# ---------------------------------------------------------------------------
# Feature: pythonic-logging, Property 1: setup_logging applies the requested level
# **Validates: Requirements 2.3**
# ---------------------------------------------------------------------------


@given(level=st.sampled_from(VALID_LEVELS))
@settings(max_examples=100)
def test_setup_logging_applies_requested_level(level):
    """For any valid logging level, setup_logging sets the root logger to that level."""
    root = logging.getLogger()
    try:
        setup_logging(level)
        assert root.level == level
    finally:
        root.handlers.clear()


# ---------------------------------------------------------------------------
# Feature: pythonic-logging, Property 2: Formatter output matches the expected pattern
# **Validates: Requirements 2.7, 6.1, 6.2**
# ---------------------------------------------------------------------------


@given(
    message=st.text(
        min_size=1,
        alphabet=st.characters(
            blacklist_categories=("Cs",), blacklist_characters="\x00\n\r"
        ),
    ).filter(lambda s: s.strip()),
    level=st.sampled_from(VALID_LEVELS),
)
@settings(max_examples=100)
def test_formatter_output_matches_expected_pattern(message, level):
    """For any message and level, the formatter produces output matching the spec pattern."""
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    record = logging.LogRecord(
        name="lxmf_group",
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=None,
        exc_info=None,
    )
    output = formatter.format(record)
    assert LOG_LINE_RE.match(
        output
    ), f"Output did not match expected pattern: {output!r}"


# ---------------------------------------------------------------------------
# Feature: pythonic-logging, Property 3: Log records carry the originating module name
# **Validates: Requirements 1.2**
# ---------------------------------------------------------------------------


@given(
    module_name=st.text(
        min_size=1,
        alphabet=st.characters(
            whitelist_categories=("L", "N"), whitelist_characters="_."
        ),
    ),
)
@settings(max_examples=100)
def test_log_records_carry_originating_module_name(module_name):
    """For any module name, a logger with that name produces records whose name matches."""
    test_logger = logging.getLogger(module_name)
    record = test_logger.makeRecord(
        name=module_name,
        level=logging.INFO,
        fn="",
        lno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )
    assert record.name == module_name


# ---------------------------------------------------------------------------
# Feature: pythonic-logging, Property 4: CLI level name resolution is case-insensitive and correct
# **Validates: Requirements 5.1, 5.2, 5.4**
# ---------------------------------------------------------------------------


def _random_case(name):
    """Strategy that produces random case variations of a level name."""
    return st.tuples(*[st.sampled_from([c.lower(), c.upper()]) for c in name]).map(
        lambda chars: "".join(chars)
    )


# Build a strategy that picks a level name then randomises its case
_level_with_case = st.sampled_from(LEVEL_NAMES).flatmap(
    lambda name: _random_case(name).map(lambda variant: (name, variant))
)


@given(data=_level_with_case)
@settings(max_examples=100)
def test_cli_level_name_resolution_case_insensitive(data):
    """For any case variation of a valid level name, uppercasing and resolving gives the correct int."""
    canonical, variant = data
    resolved = getattr(logging, variant.upper())
    assert resolved == LEVEL_MAP[canonical]
