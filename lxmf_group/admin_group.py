"""AdminGroup — admin bot for server-level group management."""

import logging
import os.path
from typing import Any

import RNS

from .base_group import BaseGroup
from .helpers import qr_unicode
from .interfaces import ServerInterface

logger: logging.Logger = logging.getLogger(__name__)


class AdminGroup(BaseGroup):
    """Admin-only LXMF bot for managing groups."""

    _kind: str = "Admin Group"

    def __init__(self, server: ServerInterface) -> None:
        self.data_dir = os.path.join(server.data_dir, "admin")
        if not os.path.exists(self.data_dir):
            identity, address = self._generate_identity()
            self._create_data_dir(data_dir=self.data_dir, identity=identity)
            name_suffix = address[-4:]
            self.name = f"Admin Group {name_suffix}"

        super().__init__(self.data_dir, server)

    def show_admin_claim(self):
        if not self._all_members():
            self._setup_admin_claim()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _register_commands(self) -> None:
        super()._register_commands()

        @self.bot.command(
            name="admin", description="Add an admin to the Admin Group",
            usage="/admin <address>", admin_only=True,
        )
        def cmd_admin(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /admin <address>")
                return
            if self._is_member(address):
                ctx.reply(f"{address} is already an admin.")
                return
            self._add_member(address, is_admin=True)
            self._broadcast(f"{address} has been added as admin.", exclude={address})

        @self.bot.command(
            name="list_groups", description="List all running groups", admin_only=True,
        )
        def list_groups(ctx: Any) -> None:
            entries = self.server.list_group_names()
            if not entries:
                ctx.reply("No groups running")
                return
            lines = ["Groups on this server:"]
            for display_name, address in entries:
                lines.append(self._format_address(display_name, address))
            ctx.reply("\n".join(lines))

        @self.bot.command(
            name="group_info", description="Show details of a group", admin_only=True,
        )
        def group_info(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /group_info <address>")
                return
            group = self.server.find_group(address)
            if not group:
                ctx.reply(f"Error: Group '{address}' not found")
                return
            lines = [
                f"Name: {group.name}",
                f"Address: {group.destination_hash_str()}",
                f"Members: {group._member_count()}",
                f"Visibility: {'Public' if group.is_public else 'Private'}",
            ]
            if group.description:
                lines.append(f"Description: {group.description}")
            if group.claim_token:
                lines.append(f"Claim token: {group.claim_token}")
            ctx.reply("\n".join(lines))

        @self.bot.command(
            name="create_group", description="Create a new group", admin_only=True,
        )
        def create_group(ctx: Any) -> None:
            name = " ".join(ctx.args) if ctx.args else ""
            if not name:
                ctx.reply("Usage: /create_group <name>")
                return
            try:
                group = self.server.create_group(name, creator=ctx.sender)
            except Exception as e:
                ctx.reply(f"Error: {e}")
                return
            addr = group.destination_hash_str()
            ctx.reply(f"Group created: {name}\nAddress: {addr}")
            group.bot.send(ctx.sender, f"Welcome to {name}! You are the group admin.")

        @self.bot.command(
            name="remove_group", description="Remove a group by address", admin_only=True,
        )
        def remove_group(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /remove_group <address>")
                return
            try:
                self.server.remove_group(address)
            except Exception as e:
                ctx.reply(f"Error: {e}")
                return
            ctx.reply(f"Group removed: {address}")

        @self.bot.command(
            name="rename_group", description="Rename a group", admin_only=True,
        )
        def rename_group(ctx: Any) -> None:
            if len(ctx.args) < 2:
                ctx.reply("Usage: /rename_group <address> <new_name>")
                return
            address = ctx.args[0]
            new_name = " ".join(ctx.args[1:])
            group = self.server.find_group(address)
            if not group:
                ctx.reply(f"Error: Group '{address}' not found")
                return
            old_name = group.name
            group.name = new_name
            group._broadcast(f"Renamed from '{old_name}' to '{new_name}'.")
            ctx.reply(f"Group renamed: {address} -> {new_name}")

        @self.bot.command(
            name="assign_admin", description="Assign an admin to a group", admin_only=True,
        )
        def assign_admin(ctx: Any) -> None:
            if len(ctx.args) < 2:
                ctx.reply("Usage: /assign_admin <group_address> <user_hash>")
                return
            group_address = ctx.args[0]
            user_hash = ctx.args[1]
            group = self.server.find_group(group_address)
            if not group:
                ctx.reply(f"Error: Group '{group_address}' not found")
                return
            if not group._is_member(user_hash):
                group._add_member(user_hash)
            group._promote_to_admin(user_hash)
            group.bot.send(
                user_hash,
                f"Welcome! You have been assigned as admin of {group.name}.",
            )
            ctx.reply(f"Admin assigned: {user_hash} -> {group.name}")

        @self.bot.command(
            name="remove_admin", description="Remove an admin from a group", admin_only=True,
        )
        def remove_admin(ctx: Any) -> None:
            if len(ctx.args) < 2:
                ctx.reply("Usage: /remove_admin <group_address> <user_hash>")
                return
            group_address = ctx.args[0]
            user_hash = ctx.args[1]
            group = self.server.find_group(group_address)
            if not group:
                ctx.reply(f"Error: Group '{group_address}' not found")
                return
            if not group._is_admin(user_hash):
                ctx.reply("User is not an admin of this group.")
                return
            group._demote_from_admin(user_hash)
            group.bot.send(
                user_hash,
                f"You have been removed as admin of {group.name}.",
            )
            ctx.reply(f"Admin removed: {user_hash} from {group.name}")

    # ------------------------------------------------------------------
    # Message handler — claim token + admin gate
    # ------------------------------------------------------------------

    def _register_message_handler(self) -> None:

        @self.bot.on_message()
        def handle_message(sender: str, message: Any) -> bool:
            content = message.content.decode("utf-8").strip()

            # Claim token
            if self.claim_token and content == self.claim_token:
                self._add_member(sender, is_admin=True)
                self.claim_token = None
                logger.critical("Admin Group admin claimed by %s", sender)
                self.bot.send(sender, "You are now admin of the Admin Group.")
                return True

            if not self._is_member(sender):
                self.bot.send(
                    sender, "You need to be an Admin Group member to use this service."
                )
                return True

            return False

    # ------------------------------------------------------------------
    # Admin claim token
    # ------------------------------------------------------------------

    def _setup_admin_claim(self) -> None:
        """Generate and log a one-time claim token."""
        token = RNS.hexrep(RNS.Identity.get_random_hash()[:8], delimit=False)
        self.claim_token = token
        logger.critical("  No admin defined for %s.", self._kind)
        logger.critical("  Send this token to claim admin:")
        logger.critical("")
        logger.critical("    %s", token)
        logger.critical("")
        qr_text = qr_unicode(token)
        if qr_text:
            for line in qr_text.splitlines():
                logger.critical("%s", line)
            logger.critical("")
        logger.critical("  This token can only be used once.")
        logger.critical("")
