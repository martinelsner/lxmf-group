# Configuration

lxmf-group stores all state in a data directory. The default location is platform-specific, determined by [platformdirs](https://pypi.org/project/platformdirs/):

- Linux: `~/.local/share/lxmf-group/`
- macOS: `~/Library/Application Support/lxmf-group/`
- Windows: `C:\Users\<user>\AppData\Local\lxmf-group\`

Override with `--data <path>`.

## Directory layout

```text
~/.local/share/lxmf-group/
├── admin/                      ← Admin Group
│   ├── identity                ← RNS identity file
│   └── storage/                ← JSON storage (name, permissions, etc.)
└── groups/
    └── a1b2c3d4e5f6.../       ← one directory per group
        ├── identity
        └── storage/
```

Each group directory is named after its LXMF address hash. The `identity` file contains the group's RNS identity. The `storage/` directory contains JSON files managed by LXMFy (group name, description, visibility, permissions, etc.).

## Creating groups

Groups are created via the Admin Group's `/create_group <name>` command. This creates the directory, generates an identity, seeds the name and creator as admin, and starts the group.

## Group state

All group state lives in `storage/` as JSON files:

- `name.json` — group display name
- `description.json` — group description
- `is_public.json` — public/private visibility
- `permissions:user_roles.json` — role assignments (who is a member, who is admin)

These are managed by LXMFy's storage and permission systems. You generally don't need to edit them manually.

## Reticulum

The server initializes a single RNS Reticulum instance using the default system config (`~/.reticulum/config`). All groups share this instance. An alternate config directory can be specified with `--rnsconfig <path>`.

```bash
nano ~/.reticulum/config
```
