"""Server — manages the collection of running groups."""

import logging
import os.path
import queue
import shutil
import sys
import threading
import time
from typing import Generator

import platformdirs
import RNS

from .admin_group import AdminGroup
from .group import Group
from .interfaces import ServerInterface

logger = logging.getLogger(__name__)


class Server(ServerInterface):
    """Holds the shared RNS instance and the list of running groups."""

    def __init__(self, data_dir: str = None, rnsconfig: str = None):
        self.data_dir = self._setup_data_dir(data_dir)
        self.groups_dir = self._setup_groups_dir(self.data_dir)

        # Initialize Reticulum once with the default system config before
        # any LXMFBot instances are created.  Each bot will attempt its own
        # RNS.Reticulum() call, hit the "already running" guard, and reuse
        # this instance.
        RNS.Reticulum(configdir=rnsconfig)

        admin_group_data_dir = AdminGroup.ensure(server=self)
        self.admin_group = AdminGroup(server=self, data_dir=admin_group_data_dir)
        self.admin_group.setup()
        self.admin_group.start()
        self.admin_group.show_admin_claim()

        self.groups: list[Group] = list(self._start_groups())

        self._pending: queue.Queue = queue.Queue()

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

    def tick(self):
        """Drain the pending-task queue. Call from the main thread."""
        while not self._pending.empty():
            try:
                task = self._pending.get_nowait()
                task()
            except queue.Empty:
                break
            except Exception as e:
                logger.error("Error in pending task: %s", e)

    def create_group(self, name: str, creator: str):
        """Create a new group and schedule its startup.

        Returns the newly created and started Group.
        """
        group_path = Group.create(self.groups_dir, name, admin=creator)

        # Schedule actual startup on the main thread.
        done = threading.Event()
        result = {}

        def _do_start():
            try:
                g = Group(data_dir=group_path, server=self)
                g.setup()
                g.start()
                self.groups.append(g)
                logger.critical(
                    "Group created and started: %s (%s)",
                    name, os.path.basename(group_path),
                )
                result["group"] = g
            except Exception as e:
                result["error"] = str(e)
            finally:
                done.set()

        self._pending.put(_do_start)
        done.wait(timeout=30)

        if not done.is_set():
            raise RuntimeError("Group setup timed out")
        if "group" in result:
            return result["group"]
        raise RuntimeError(result.get("error", "Unknown error"))

    def remove_group(self, address: str):
        """Stop and remove a group by its LXMF address hash."""
        address = address.strip()
        if not address:
            raise ValueError("Invalid group address")

        target = None
        for g in self.groups:
            if g.destination_hash_str() == address:
                target = g
                break

        if target is None:
            raise ValueError(f"Group with address '{address}' not found")

        group_path = target.data_dir
        target.stop()
        self.groups.remove(target)
        shutil.rmtree(group_path)
        logger.critical("Group removed: %s", address)

    def find_group(self, address: str):
        """Find a running group by its LXMF address hash."""
        address = address.strip()
        for g in self.groups:
            if g.destination_hash_str() == address:
                return g
        return None

    def list_group_names(self) -> list[tuple[str, str]]:
        """Return a list of (display_name, address) for running groups."""
        return [
            (g.name or "?", g.destination_hash_str())
            for g in self.groups
        ]

    def _start_groups(self) -> Generator[Group, None, None]:
        for entry in sorted(os.listdir(self.groups_dir)):
            group_data_dir = os.path.join(self.groups_dir, entry)
            if not os.path.isdir(group_data_dir):
                continue
            logger.info("Starting group: %s", entry)
            try:
                g = Group(data_dir=group_data_dir, server=self)
                g.setup()
                g.start()
                yield g
            except Exception as e:
                logger.exception("Failed to start group at %s: %s", group_data_dir, e)

    def run(self):
        """Block forever, processing pending tasks."""
        try:
            while True:
                self.tick()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Terminated by CTRL-C")
            sys.exit(0)
