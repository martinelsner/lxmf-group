"""BaseGroup — shared foundation for AdminGroup and Group.

Both AdminGroup and Group are LXMFy-based bots that share a common
lifecycle (setup / start / stop), permission-based membership, help
formatting, and name-resolution logic.

Membership and admin status are managed entirely through LXMFy's
PermissionManager role system:
  - A "member" is anyone who has been assigned any role.
  - An "admin" is anyone with the "admin" role.
"""

import logging
import os
import threading
from functools import cache, cached_property
from typing import Any

import msgpack
import RNS
from lxmfy import DefaultPerms, JSONStorage, LXMFBot
from lxmfy.help import HelpFormatter, HelpSystem

from .helpers import CommandDict, qr_unicode, short_hash
from .interfaces import ServerInterface
from .constants import ANNOUNCE_INTERVAL

logger: logging.Logger = logging.getLogger(__name__)


class BaseGroup:
    """Abstract base for any LXMFy-backed bot group."""

    _thread: threading.Thread | None = None
    _kind: str = "Group"

    def __init__(self, data_dir: str, server: ServerInterface) -> None:
        self.data_dir = data_dir
        self.server = server
        self.claim_token: str | None = None

        self.bot: LXMFBot = LXMFBot(
            name=self.name or self._kind,
            announce=ANNOUNCE_INTERVAL,
            announce_enabled=True,
            announce_immediately=True,
            command_prefix="/",
            config_path=data_dir,
            storage_type="json",
            storage_path=self._storage_dir(data_dir),
            first_message_enabled=False,
            permissions_enabled=True,
            # Don't enable message_persistence — it replays already-delivered
            # messages on restart because the queue is persisted before delivery
            # is confirmed, causing duplicates for all group members.
            message_persistence_enabled=False,
            autopeer_propagation=True,
        )

        self.bot.commands = CommandDict(self.bot.commands)

        # Sync bot.admins from the permissions system so admin_only commands work.
        for user, roles in self.bot.permissions.user_roles.items():
            if "admin" in roles:
                self.bot.admins.add(user)

        self._install_help_system()

        @self.bot.command(name="?", description="Show help for commands")
        def help_alias(ctx: Any) -> None:
            self.bot.commands["help"].callback(ctx)

        self._register_commands()
        self._register_message_handler()

    # ------------------------------------------------------------------
    # Storage properties
    # ------------------------------------------------------------------

    @cached_property
    def _storage(self) -> JSONStorage:
        return JSONStorage(self._storage_dir(self.data_dir))

    @property
    def name(self) -> str:
        return self._storage.get("name", "")

    @name.setter
    def name(self, value: str) -> None:
        self._storage.set("name", value)
        # Update the LXMF announce display name and re-announce.
        if self.bot.local:
            self.bot.local.display_name = value
            self.bot.local.announce()

    @property
    def description(self) -> str:
        return self._storage.get("description", "")

    @description.setter
    def description(self, value: str) -> None:
        self._storage.set("description", value)

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_identity() -> tuple[RNS.Identity, str]:
        """Generate a new RNS identity and derive its LXMF address hex."""
        identity = RNS.Identity()
        dest_hash = RNS.Destination.hash_from_name_and_identity(
            "lxmf.delivery", identity
        )
        return identity, RNS.hexrep(dest_hash, delimit=False)

    @staticmethod
    def _create_data_dir(data_dir: str, identity: RNS.Identity) -> None:
        """Create a group directory and write the identity file into it."""
        os.makedirs(data_dir, exist_ok=False)
        identity.to_file(os.path.join(data_dir, "identity"))
        os.makedirs(BaseGroup._storage_dir(data_dir), exist_ok=True)

    @staticmethod
    @cache
    def _storage_dir(data_dir: str) -> str:
        return os.path.join(data_dir, "storage")

    def destination_hash_str(self) -> str:
        if self.bot.local:
            return RNS.hexrep(self.bot.local.hash, delimit=False)
        return ""

    # ------------------------------------------------------------------
    # Membership via LXMFy permissions
    # ------------------------------------------------------------------

    def _is_admin(self, user_hash: str) -> bool:
        return self.bot.permissions.has_permission(user_hash, DefaultPerms.ALL)

    def _is_member(self, user_hash: str) -> bool:
        return user_hash in self.bot.permissions.user_roles

    def _add_member(self, user_hash: str, is_admin: bool = False) -> None:
        """Add a user as member, optionally as admin."""
        self.bot.permissions.assign_role(user_hash, "user")
        if is_admin:
            self.bot.permissions.assign_role(user_hash, "admin")
            self.bot.admins.add(user_hash)
        self.bot.send(
            user_hash,
            f"Welcome to {self.name}! Use /help to see what you can do here.",
        )

    def _remove_member(self, user_hash: str) -> None:
        """Remove a user entirely from the permissions system."""
        if user_hash in self.bot.permissions.user_roles:
            del self.bot.permissions.user_roles[user_hash]
            self.bot.permissions.save_data()
        self.bot.admins.discard(user_hash)

    def _all_members(self) -> set[str]:
        """Return the set of all user hashes that have any role."""
        return set(self.bot.permissions.user_roles.keys())

    def _member_count(self) -> int:
        return len(self.bot.permissions.user_roles)

    def _display(self, user_hash: str) -> str:
        """Return 'Name !abcd' or just '!abcd' for a user.

        Resolves the display name from the RNS announce cache.
        """
        name = self._recall_name(user_hash)
        tag = short_hash(user_hash)
        return f"{name} {tag}" if name else tag

    @staticmethod
    def _format_address(name: str, address: str) -> str:
        """Return 'Name <address>' or '<address>' if name is empty."""
        return f"{name} <{address}>" if name else f"<{address}>"

    def _recall_name(self, user_hash: str) -> str:
        """Best-effort display name from the RNS announce cache."""
        try:
            raw_hash = bytes.fromhex(user_hash)
        except ValueError:
            logger.debug("_recall_name: invalid hex hash %s", user_hash)
            return ""

        app_data = RNS.Identity.recall_app_data(raw_hash)
        if app_data is None:
            logger.debug("_recall_name: no app_data cached for %s", user_hash)
            return ""

        logger.debug("_recall_name: raw app_data for %s: %r", user_hash, app_data)

        # Some clients (Meshchat, Sideband) pack app_data as msgpack [name, ...]
        try:
            unpacked = msgpack.unpackb(app_data)
            if isinstance(unpacked, list) and unpacked:
                name = unpacked[0]
                if isinstance(name, bytes):
                    name = name.decode("utf-8")
                if name:
                    return str(name)
        except Exception:
            pass

        # Other clients (Columba) send plain UTF-8
        try:
            return app_data.decode("utf-8")
        except Exception:
            logger.debug("_recall_name: could not decode app_data for %s", user_hash)
            return ""

    # ------------------------------------------------------------------
    # Broadcast
    # ------------------------------------------------------------------

    def _broadcast(self, content: str, exclude: set[str] | None = None) -> None:
        exclude = exclude or set()
        for user_hash in self._all_members():
            if user_hash not in exclude:
                self.bot.send(user_hash, content)

    # ------------------------------------------------------------------
    # Help system
    # ------------------------------------------------------------------

    def _install_help_system(self) -> None:
        prefix = self.bot.command_prefix or ""

        class _Fmt(HelpFormatter):
            @staticmethod
            def format_command(command: Any) -> str:
                lines = [f"{prefix}{command.name}: {command.help.description}"]
                if command.help.usage:
                    lines.append(f"  Usage: {command.help.usage}")
                if command.help.examples:
                    lines.append("  Examples:")
                    lines.extend(f"    {ex}" for ex in command.help.examples)
                return "\n".join(lines)

            @staticmethod
            def format_all_commands(categories: dict[str, Any]) -> str:
                lines = ["Available commands:"]
                for _cat, cmds in categories.items():
                    for cmd in cmds:
                        lines.append(f"{prefix}{cmd.name} — {cmd.help.description}")
                return "\n".join(lines)

        self.bot.help_system = HelpSystem(self.bot, formatter=_Fmt())

    # ------------------------------------------------------------------
    # Common commands
    # ------------------------------------------------------------------

    def _register_commands(self) -> None:
        """Register commands common to every group.

        Subclasses should call super()._register_commands() and then
        register their own additional commands.
        """

        @self.bot.command(name="info", description="Show group details")
        def cmd_info(ctx: Any) -> None:
            if not self._is_member(ctx.sender):
                ctx.reply(f"You are not a member of this {self._kind}.")
                return
            addr = self.destination_hash_str() or "?"
            lines = [
                f"Name: {self.name}",
                f"Description: {self.description}",
                f"Address: {addr}",
                f"Members: {self._member_count()}",
            ]
            lines.extend(self._info_extra_lines())
            ctx.reply("\n".join(l for l in lines if l is not None))

        @self.bot.command(name="members", description="List members")
        def cmd_members(ctx: Any) -> None:
            if not self._is_member(ctx.sender):
                ctx.reply(f"You are not a member of this {self._kind}.")
                return
            members = self._all_members()
            if not members:
                ctx.reply("No members.")
                return
            lines = [f"Members ({len(members)}):"]
            for h in sorted(members):
                role = "admin" if self._is_admin(h) else "user"
                label = self._format_address(self._recall_name(h), h)
                lines.append(f"{label} [{role}]")
            ctx.reply("\n".join(lines))

        @self.bot.command(
            name="kick",
            description="Remove a user",
            usage="/kick <address>",
            admin_only=True,
        )
        def cmd_kick(ctx: Any) -> None:
            address = ctx.args[0] if ctx.args else ""
            if not address:
                ctx.reply("Usage: /kick <address>")
                return
            if self._is_admin(address):
                ctx.reply("Cannot remove an admin. Use the Admin Group instead.")
                return
            if not self._is_member(address):
                ctx.reply("User is not a member.")
                return
            self._remove_member(address)
            self.bot.send(address, f"You have been removed from {self.name}.")
            self._broadcast(f"{address} has been removed.", exclude={address})
            ctx.reply(f"Removed {address}.")

        @self.bot.command(
            name="name",
            description="Rename this group",
            usage="/name <new_name>",
            admin_only=True,
        )
        def cmd_name(ctx: Any) -> None:
            new_name = " ".join(ctx.args) if ctx.args else ""
            if not new_name:
                ctx.reply("Usage: /name <new_name>")
                return
            old_name = self.name
            self.name = new_name
            self._broadcast(f"Renamed from '{old_name}' to '{new_name}'.")

        @self.bot.command(
            name="description",
            description="Set the group description",
            usage="/description <text>",
            admin_only=True,
        )
        def cmd_description(ctx: Any) -> None:
            desc = " ".join(ctx.args) if ctx.args else ""
            self.description = desc
            if desc:
                ctx.reply(f"Description set to: {desc}")
            else:
                ctx.reply("Description cleared.")

        @self.bot.command(name="leave", description="Leave this group")
        def cmd_leave(ctx: Any) -> None:
            if not self._is_member(ctx.sender):
                ctx.reply(f"You are not a member of this {self._kind}.")
                return
            if self._is_admin(ctx.sender):
                ctx.reply(
                    "Admins cannot leave. Ask an Admin Group admin to remove you."
                )
                return
            self._remove_member(ctx.sender)
            ctx.reply(f"You have left the {self._kind}.")
            self._broadcast(f"{ctx.sender} has left.")

    # ------------------------------------------------------------------
    # Extension points
    # ------------------------------------------------------------------

    def _info_extra_lines(self) -> list[str | None]:
        return []

    def _register_message_handler(self) -> None:
        raise NotImplementedError

    def _show_qr_code(self) -> None:
        """Log address and QR code."""
        label = self._kind
        logger.critical("")
        logger.critical("=" * 75)
        logger.critical("%s: %s", label, self.name)
        logger.critical("=" * 75)
        logger.critical("")
        if self.bot.local:
            logger.critical(
                "LXMF Address: %s",
                RNS.prettyhexrep(self.bot.local.hash),
            )
            dest_hex = RNS.hexrep(self.bot.local.hash, delimit=False)
            pub_hex = RNS.hexrep(self.bot.identity.get_public_key(), delimit=False)
            lxma_url = "lxma://" + dest_hex + ":" + pub_hex
            logger.critical("Columba link: %s", lxma_url)
            logger.critical("")
            qr_text = qr_unicode(lxma_url)
            if qr_text:
                for line in qr_text.splitlines():
                    logger.critical("%s", line)
                logger.critical("")
        logger.critical("")

    def start(self) -> None:
        self._thread = threading.Thread(target=self.bot.run, args=(1,), daemon=True)
        self._thread.start()
        self._show_qr_code()

    def stop(self) -> None:
        self.bot.cleanup()
