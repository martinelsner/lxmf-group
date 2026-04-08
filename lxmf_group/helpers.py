"""Pure utility functions that don't hold per-group state."""

import logging
import os
import sys

import qrcode


class CommandDict(dict):
    """Dict subclass that normalises keys so command lookup is
    case-insensitive and treats ``-`` / ``_`` as identical.

    Commands are stored under their *original* name (so help text keeps the
    canonical spelling) but every lookup goes through ``_norm``.
    """

    @staticmethod
    def _norm(key):
        return key.lower().replace("-", "_") if isinstance(key, str) else key

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        nk = self._norm(key)
        if nk != key:
            super().__setitem__(nk, value)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return super().__getitem__(self._norm(key))

    def __contains__(self, key):
        return super().__contains__(key) or super().__contains__(self._norm(key))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def values(self):
        """Yield each command only once (skip normalised aliases)."""
        seen = set()
        for v in super().values():
            vid = id(v)
            if vid not in seen:
                seen.add(vid)
                yield v


def short_hash(address: str) -> str:
    """Shorten a hex address to last 4 characters, Meshtastic-style."""
    if len(address) >= 4:
        return "!" + address[-4:]
    return address


def qr_unicode(data: str) -> str:
    """Render a QR code using half-block characters.

    Uses block-element characters so the output is readable on any
    background without relying on ANSI colour escapes.
    """
    try:
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        rows = len(matrix)
        DARK = "\u2588"
        LIGHT = "\u2591"
        TOP_DARK = "\u2580"
        BOT_DARK = "\u2584"
        lines = []
        for y in range(0, rows, 2):
            line = ""
            for x in range(len(matrix[0])):
                top = matrix[y][x]
                bottom = matrix[y + 1][x] if y + 1 < rows else False
                if top and bottom:
                    line += DARK
                elif top and not bottom:
                    line += TOP_DARK
                elif not top and bottom:
                    line += BOT_DARK
                else:
                    line += LIGHT
            lines.append(line)
        return "\n".join(lines)
    except Exception:
        return ""


def setup_logging(level: int) -> None:
    """Configure the root logger with console output."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    if os.environ.get("INVOCATION_ID"):
        console_fmt = "[%(levelname)s] %(message)s"
    else:
        console_fmt = "[%(asctime)s] [%(levelname)s] %(message)s"

    formatter = logging.Formatter(fmt=console_fmt, datefmt="%Y-%m-%d %H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root_logger.addHandler(console)
