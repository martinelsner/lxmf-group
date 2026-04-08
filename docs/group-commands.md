# Group commands

Commands available in normal groups. All commands start with `/`. Any message that does not start with `/` is relayed to all group members. Hyphens and underscores are interchangeable (e.g. `/create-group` = `/create_group`).

Type `/help` or `/?` to see available commands.

## Everyone

| Command | Description |
|---------|-------------|
| `/help`, `/?` | Show available commands |
| `/info` | Show group name, description, address, member count, visibility |
| `/members` | List all members with their role |
| `/leave` | Leave the group (admins cannot leave) |

## Admin only

| Command | Description |
|---------|-------------|
| `/add <address>` | Add a user to the group |
| `/admin <address>` | Add or promote a user to admin |
| `/kick <address>` | Remove a user (cannot kick admins) |
| `/name <new_name>` | Rename the group |
| `/description <text>` | Set group description (empty clears it) |
| `/public` | Make the group public (anyone can join) |
| `/private` | Make the group private (invite only) |
| `/delete` | Delete the group permanently |

## Joining

**Public group** — send any message to the group's LXMF address. You're added automatically.

**Private group** — an admin must add you with `/add <your_address>`.
