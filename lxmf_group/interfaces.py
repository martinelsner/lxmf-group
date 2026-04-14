"""Abstract interface for the Server, used to avoid circular imports."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .group import Group


class ServerInterface(ABC):

    data_dir: str
    groups_dir: str
    groups: list[Group]
    propagation_node: str | None
