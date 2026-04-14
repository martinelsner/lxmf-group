"""Allow running with ``python -m lxmf_group`` or via the console script."""

import argparse
import logging

from .constants import DESCRIPTION, NAME, VERSION
from .helpers import setup_logging
from .server import Server


def main():
    parser = argparse.ArgumentParser(description=f"{NAME} - {DESCRIPTION}")

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    parser.add_argument(
        "-d", "--data", type=str, default=None,
        help="Server data directory (groups live under <data>/groups/)",
    )
    parser.add_argument(
        "-l", "--loglevel", type=str.upper, default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--rnsconfig", type=str, default=None,
        help="Path to alternative Reticulum config directory",
    )
    parser.add_argument(
        "-p", "--propagation-node", type=str, default=None,
        help="Destination hash of the propagation node to use for message sync",
    )

    params = parser.parse_args()
    setup_logging(getattr(logging, params.loglevel))

    server = Server(
        data_dir=params.data,
        rnsconfig=params.rnsconfig,
        propagation_node=params.propagation_node,
    )
    server.run()


if __name__ == "__main__":
    main()
