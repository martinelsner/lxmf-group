"""Server — manages the shared RNS instance and the event loop."""

import logging
import os.path
import sys
import time
from typing import Generator

import platformdirs
import RNS

from .admin_group import AdminGroup
from .group import Group
from .interfaces import ServerInterface

logger = logging.getLogger(__name__)


class Server(ServerInterface):
    """Holds the shared RNS instance and delegates group management to AdminGroup."""

    def __init__(self, data_dir: str = None, rnsconfig: str = None):
        self.data_dir = self._setup_data_dir(data_dir)
        self.groups_dir = self._setup_groups_dir(self.data_dir)
        self.groups: list[Group] = []

        # Initialize Reticulum once with the default system config before
        # any LXMFBot instances are created.  Each bot will attempt its own
        # RNS.Reticulum() call, hit the "already running" guard, and reuse
        # this instance.
        RNS.Reticulum(configdir=rnsconfig)

        admin_group_data_dir = AdminGroup.setup(server=self)
        self.admin_group = AdminGroup(server=self, data_dir=admin_group_data_dir)
        self.admin_group.start()

        self.groups.extend(self._start_groups())

    @staticmethod
    def _setup_data_dir(data_dir: str = None) -> str:
        if data_dir is not None:
            data_dir = data_dir.strip()
        if not data_dir:
            data_dir = platformdirs.user_data_dir("lxmf-group")
        data_dir = data_dir.rstrip("/")
        os.makedirs(data_dir, exist_ok=True)
        logger.info("Data dir: %s", data_dir)
        return data_dir

    @staticmethod
    def _setup_groups_dir(data_dir: str) -> str:
        groups_dir = os.path.join(data_dir, "groups")
        os.makedirs(groups_dir, exist_ok=True)
        logger.info("Groups dir: %s", groups_dir)
        return groups_dir

    def _start_groups(self) -> Generator[Group, None, None]:
        for entry in sorted(os.listdir(self.groups_dir)):
            group_data_dir = os.path.join(self.groups_dir, entry)
            if not os.path.isdir(group_data_dir):
                continue
            logger.info("Starting group: %s", entry)
            try:
                group = Group(data_dir=group_data_dir, server=self)
                group.on_delete = self.admin_group._handle_group_delete
                group.start()
                yield group
            except Exception as e:
                logger.exception("Failed to start group at %s: %s", group_data_dir, e)

    def run(self):
        """Block forever, processing pending tasks."""
        try:
            while True:
                self.admin_group.tick()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Terminated by CTRL-C")
            sys.exit(0)
