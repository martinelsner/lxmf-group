"""Tests for CommandDict — case-insensitive, dash/underscore-agnostic lookup."""

import pytest

from lxmf_group.helpers import CommandDict


@pytest.fixture
def cd():
    d = CommandDict()
    d["create_group"] = "create_group_handler"
    d["help"] = "help_handler"
    return d


# --- case insensitivity ---


@pytest.mark.parametrize(
    "key", ["create_group", "Create_Group", "CREATE_GROUP", "cReAtE_gRoUp"]
)
def test_lookup_case_insensitive(cd, key):
    assert cd[key] == "create_group_handler"


@pytest.mark.parametrize("key", ["create_group", "Create_Group", "CREATE_GROUP"])
def test_contains_case_insensitive(cd, key):
    assert key in cd


# --- dash / underscore interchangeable ---


@pytest.mark.parametrize("key", ["create-group", "Create-Group", "CREATE-GROUP"])
def test_lookup_dash_for_underscore(cd, key):
    assert cd[key] == "create_group_handler"


@pytest.mark.parametrize("key", ["create-group", "Create-Group"])
def test_contains_dash_for_underscore(cd, key):
    assert key in cd


# --- .get() ---


def test_get_normalised(cd):
    assert cd.get("CREATE-GROUP") == "create_group_handler"


def test_get_missing_returns_default(cd):
    assert cd.get("nonexistent", "nope") == "nope"


# --- miss still raises KeyError ---


def test_missing_key_raises(cd):
    with pytest.raises(KeyError):
        cd["no_such_command"]


# --- canonical name preserved ---


def test_canonical_key_preserved(cd):
    """The original key is still present so help text uses the registered name."""
    assert "create_group" in dict.keys(cd)
