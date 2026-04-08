"""Group — LXMFy-based group chat bot.

Each group runs as an independent LXMFBot on its own thread.
Groups have two roles via LXMFy's PermissionManager: admin and user.

Normal users can send/receive messages and view group details.
Admins can invite/remove users, change group settings, and delete the group.

A group can be public (anyone can join by sending a message) or private
(only invited users can join).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable

from lxmfy import JSONStorage

from .base_group import BaseGroup

logger: logging.Logger = logging.getLogger(__name__)


class Group(BaseGroup):
    """A single distribution group backed by an LXMFBot."""

    _kind: str = "Group"
    on_delete: "Callable[[Group], None] | None" = None

    @property
    def is_public(self) -> bool:
        return self._storage.get("is_public", False)

    @is_public.setter
    def is_public(self, value: bool) -> None:
        self._storage.set("is_public", value)

    @staticmethod
    def setup(base_dir: str, name: str, admin: str) -> str:
        """Create a group subdirectory named after its LXMF address.

        Stores the group name and seeds the creator as admin in the
        storage dir so ``__init__`` picks them up on startup.

        Returns the path to the newly created group directory.
        """
        identity, addr = BaseGroup._generate_identity()
        path = os.path.join(base_dir, addr)
        BaseGroup._create_data_dir(path, identity)

        storage = JSONStorage(BaseGroup._storage_dir(path))
        storage.set("name", name)
        storage.set("permissions:user_roles", {admin: ["user", "admin"]})

        return path

    # ------------------------------------------------------------------
    # Extension points
    # ------------------------------------------------------------------

    def _info_extra_lines(self) -> list[str | None]:
        visibility = "Public" if self.is_public else "Private"
        return [f"Visibility: {visibility}"]

    def _promote_to_admin(self, user_hash: str) -> None:
        self.bot.permissions.assign_role(user_hash, "admin")
        self.bot.admins.add(user_hash)

    def _demote_from_admin(self, user_hash: str) -> None:
        self.bot.permissions.remove_role(user_hash, "admin")
        self.bot.admins.discard(user_hash)

    # ------------------------------------------------------------------
    # Group-specific commands
    # ------------------------------------------------------------------

    def _register_commands(self) -> None:
        super()._register_commands()

        @self.bot.command(
            name="add",
            description="Add a user to the group",
            usage="/add <address>",
            admin_only=True,
        )
        def cmd_add(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /add <address>")
                return
            if self._is_member(address):
                ctx.reply("User is already a member.")
                return
            self._add_member(address)
            self._broadcast(f"{address} has been added.", exclude={address})

        @self.bot.command(
            name="admin",
            description="Add or promote a user to admin",
            usage="/admin <address>",
            admin_only=True,
        )
        def cmd_admin(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /admin <address>")
                return
            if self._is_admin(address):
                ctx.reply(f"{address} is already an admin.")
                return
            if self._is_member(address):
                self._promote_to_admin(address)
                self.bot.send(
                    address, f"You have been promoted to admin of {self.name}."
                )
                self._broadcast(
                    f"{address} has been promoted to admin.", exclude={address}
                )
                return
            self._add_member(address, is_admin=True)
            self._broadcast(f"{address} has been added as admin.", exclude={address})

        @self.bot.command(
            name="public",
            description="Make the group public",
            admin_only=True,
        )
        def cmd_public(ctx: Any) -> None:
            self.is_public = True
            ctx.reply("Group is now public. Anyone can join by sending a message.")

        @self.bot.command(
            name="private",
            description="Make the group private",
            admin_only=True,
        )
        def cmd_private(ctx: Any) -> None:
            self.is_public = False
            ctx.reply("Group is now private. Only invited users can join.")

        @self.bot.command(
            name="delete",
            description="Delete this group",
            admin_only=True,
        )
        def cmd_delete(ctx: Any) -> None:
            if not self.on_delete:
                ctx.reply("Server context not available.")
                return
            self._broadcast("This group has been deleted.")
            try:
                self.on_delete(self)
                ctx.reply("Group deleted.")
            except Exception as e:
                ctx.reply(f"Error: {e}")

    # ------------------------------------------------------------------
    # Message handler — group chat relay
    # ------------------------------------------------------------------

    def _register_message_handler(self) -> None:

        @self.bot.on_message()
        def handle_message(sender: str, message: Any) -> bool:
            content = message.content.decode("utf-8").strip()

            # Handle admin claim token
            if self.claim_token and content == self.claim_token:
                self._add_member(sender, is_admin=True)
                self.claim_token = None
                logger.critical("Group admin claimed by %s", sender)
                self.bot.send(sender, f"You are now admin of {self.name}.")
                return True

            # Participant — relay message to everyone else
            if self._is_member(sender):
                prefix = self.bot.command_prefix or ""
                if prefix and content.startswith(prefix):
                    return False  # let the framework handle commands
                display = self._display(sender)
                relay = f"{display}: {content}"
                for user_hash in self._all_members():
                    if user_hash != sender:
                        self.bot.send(user_hash, relay)
                return True

            # Not a member — auto-join if public
            if self.is_public:
                self._add_member(sender)
                display = self._display(sender)
                self._broadcast(f"{display} has joined the group.", exclude={sender})
                relay = f"{display}: {content}"
                for user_hash in self._all_members():
                    if user_hash != sender:
                        self.bot.send(user_hash, relay)
                return True

            self.bot.send(
                sender, "This is a private group. You need an invitation to join."
            )
            return True
