"""Program metadata."""

from lxmf_group._version import __version__ as VERSION
from datetime import timedelta

NAME = "LXMF Groups"
DESCRIPTION = "Server-Side group functions for LXMF based apps"

ANNOUNCE_INTERVAL = int(timedelta(hours=6).total_seconds())
