"""Integration test: start a group and verify join/message behavior.

Fully isolated from any running RNS instance.
"""

import json
import logging
import os

import LXMF
import pytest
import RNS

from lxmf_group.group import Group
from lxmf_group.helpers import setup_logging


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_new_user_joins_public_group(group_server, isolated_rns):
    """A brand-new LXMF identity sends a message to a public group and gets auto-added."""
    group = group_server

    client_identity = RNS.Identity()
    client_dest = RNS.Destination(
        client_identity,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        "lxmf",
        "delivery",
    )
    RNS.Identity.remember(
        packet_hash=None,
        destination_hash=client_dest.hash,
        public_key=client_identity.get_public_key(),
        app_data=None,
    )
    client_hash = RNS.hexrep(client_dest.hash, delimit=False)

    assert not group._is_member(client_hash)

    server_dest = RNS.Destination(
        group.bot.identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        "lxmf",
        "delivery",
    )
    lxm = LXMF.LXMessage(
        server_dest,
        client_dest,
        "Hello group!",
        title="",
        desired_method=LXMF.LXMessage.DIRECT,
    )
    lxm.source_hash = client_dest.hash
    lxm.destination_hash = group.bot.local.hash
    lxm.signature_validated = True
    if lxm.hash is None:
        lxm.hash = RNS.Identity.get_random_hash()

    sent = []
    group.bot.send = lambda dest, msg, **kw: sent.append((dest, msg))

    group.bot._process_message(lxm, client_hash)

    assert group._is_member(client_hash), "Client should be a member after public join"
    assert len(sent) > 0, "Server should send a welcome message"
    assert client_hash in [m[0] for m in sent]


def test_private_group_rejects_unknown_user(group_server, isolated_rns):
    """An unknown user sending to a private group gets rejected."""
    group = group_server
    group.is_public = False

    client_identity = RNS.Identity()
    client_dest = RNS.Destination(
        client_identity,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        "lxmf",
        "delivery",
    )
    RNS.Identity.remember(
        packet_hash=None,
        destination_hash=client_dest.hash,
        public_key=client_identity.get_public_key(),
        app_data=None,
    )
    client_hash = RNS.hexrep(client_dest.hash, delimit=False)

    server_dest = RNS.Destination(
        group.bot.identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        "lxmf",
        "delivery",
    )
    lxm = LXMF.LXMessage(
        server_dest,
        client_dest,
        "Let me in!",
        title="",
        desired_method=LXMF.LXMessage.DIRECT,
    )
    lxm.source_hash = client_dest.hash
    lxm.destination_hash = group.bot.local.hash
    lxm.signature_validated = True
    if lxm.hash is None:
        lxm.hash = RNS.Identity.get_random_hash()

    sent = []
    group.bot.send = lambda dest, msg, **kw: sent.append((dest, msg))

    group.bot._process_message(lxm, client_hash)

    assert not group._is_member(client_hash)
    assert len(sent) > 0
    assert "private" in sent[0][1].lower()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_rns():
    """Tear down the RNS singleton so a fresh one can be created."""
    try:
        RNS.Reticulum.exit_handler()
    except Exception:
        pass
    RNS.Reticulum._Reticulum__instance = None
    RNS.Reticulum._Reticulum__exit_handler_ran = False
    RNS.Reticulum._Reticulum__interface_detach_ran = False
    RNS.Transport.interfaces = []
    RNS.Transport.destinations = []
    RNS.Transport.jobs_running = False
    RNS.Transport.identity = None


def _write_rns_config(rns_dir, instance_name):
    os.makedirs(rns_dir, exist_ok=True)
    cfg = (
        "[reticulum]\n"
        "  enable_transport = False\n"
        "  share_instance = No\n"
        f"  instance_name = {instance_name}\n"
        "\n[logging]\n  loglevel = 2\n"
        "\n[interfaces]\n"
    )
    with open(os.path.join(rns_dir, "config"), "w") as f:
        f.write(cfg)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def isolated_rns(tmp_path):
    """Provide an isolated RNS.Reticulum instance in a temp directory."""
    setup_logging(logging.DEBUG)
    _reset_rns()
    rns_dir = str(tmp_path / "rns_config")
    instance_name = f"test_{os.getpid()}_{id(tmp_path)}"
    _write_rns_config(rns_dir, instance_name)
    rns_instance = RNS.Reticulum(configdir=rns_dir, loglevel=RNS.LOG_WARNING)
    yield rns_instance
    _reset_rns()


@pytest.fixture()
def group_server(isolated_rns, tmp_path):
    """Start a single Group inside the isolated RNS instance."""
    group_dir = str(tmp_path / "server" / "testgroup")
    os.makedirs(group_dir, exist_ok=True)

    storage_dir = os.path.join(group_dir, "storage")
    os.makedirs(storage_dir, exist_ok=True)
    for key, value in [
        ("name", "Test Group"),
        ("is_public", True),
        ("description", ""),
    ]:
        with open(os.path.join(storage_dir, f"{key}.json"), "w") as f:
            json.dump(value, f)

    # Use a stub server to avoid needing the full Server class
    class _StubServer:
        data_dir = str(tmp_path / "server")
        groups_dir = str(tmp_path / "server" / "groups")
        groups = []
        propagation_node = None

    group = Group(data_dir=group_dir, server=_StubServer())
    group._show_qr_code()
    yield group
