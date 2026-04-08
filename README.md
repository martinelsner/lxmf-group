# lxmf-group

A server-side LXMF distribution group. It receives messages and forwards them to all members — like a mailing list with chat features. Any LXMF-compatible client (Sideband, NomadNet, Columba, ...) can participate because each group acts as a standard LXMF endpoint.

Built with [LXMFy](https://git.quad4.io/LXMFy/LXMFy), a bot framework for the [Reticulum](https://reticulum.network/) network. Inspired by [lxmf_distribution_group_extended](https://github.com/SebastianObi/LXMF-Tools/tree/main/lxmf_distribution_group_extended) by [Sebastian Obele](https://github.com/SebastianObi).

## Features

- Host multiple independent groups in a single process
- Compatible with all LXMF applications (NomadNet, Sideband, Columba, ...)
- Admin Group for server-level management (create/remove/rename groups)
- Two roles per group: admin and user, managed via LXMFy's permission system
- Public groups (anyone can join) or private groups (invite only)
- New groups start as private; group admins can make them public
- Text-based command interface via LXMF messages
- One-time claim token for bootstrapping the first admin

## Current status

Beta software, work in progress.

## Installation

```bash
sudo apt update
sudo apt install python3-cryptography pipx
pipx install --system-site-packages git+https://codeberg.org/melsner/lxmf_group.git
```

Configure Reticulum to suit your network:

```bash
nano ~/.reticulum/config
```

## Running

```bash
lxmf-group
```

The server creates an Admin Group with its own LXMF address. On first run, since no admin exists yet, a one-time claim token is printed to the console. Send that token as a message to the Admin Group from your LXMF client to become admin.

## Data directory layout

The default data directory is platform-specific, determined by [platformdirs](https://pypi.org/project/platformdirs/):

- Linux: `~/.local/share/lxmf-group/`
- macOS: `~/Library/Application Support/lxmf-group/`
- Windows: `C:\Users\<user>\AppData\Local\lxmf-group\`

Override with `--data <path>`.

```text
~/.local/share/lxmf-group/
├── admin/                  ← Admin Group
│   ├── identity
│   └── storage/
└── groups/
    └── a1b2c3d4e5f6.../   ← one directory per group
        ├── identity
        └── storage/
```

All state is stored as JSON files in each group's `storage/` directory, managed by LXMFy.

## Creating groups

From the Admin Group, send:

```text
/create_group My Group Name
```

The creator is automatically assigned as admin of the new group.

## Startup parameters

```text
usage: lxmf-group [-h] [-V] [-d DATA] [--rnsconfig RNSCONFIG] [-l LOGLEVEL]

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show version and exit
  -d DATA, --data DATA  server data directory
  --rnsconfig RNSCONFIG path to alternative Reticulum config directory
  -l LOGLEVEL           log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

## Run as a systemd service

Create a dedicated system user:

```bash
sudo useradd --system --shell /usr/sbin/nologin --create-home --home-dir /var/lib/reticulum reticulum
```

Install:

```bash
sudo --user reticulum pipx install --system-site-packages git+https://codeberg.org/melsner/lxmf_group.git
```

Create `/etc/systemd/system/lxmf-group.service`:

```ini
[Unit]
Description=lxmf-group
After=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5
User=reticulum
ExecStart=/var/lib/reticulum/.local/bin/lxmf-group

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable --now lxmf-group
```

## Documentation

- [Concepts](docs/concepts.md) — groups, roles, message transport
- [Group commands](docs/group-commands.md) — commands for normal groups
- [Admin Group commands](docs/admin-group-commands.md) — server-level group management
- [Configuration](docs/configuration.md) — data directory, storage, Reticulum
- [Family group example](examples/family-group.md) — simple invite-only group setup
- [NixOS service](docs/nixos-service.md) — NixOS module and systemd service
- [Development](docs/development.md) — dev environment, tests, versioning

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## About the code

This project is written with the help of AI-based tools, directed and supervised by a human.
