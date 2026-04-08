# Admin Group commands

Commands available in the Admin Group — the server-level bot for managing groups. All commands require admin role. Only Admin Group members can interact with it.

Type `/help` or `/?` to see available commands.

## Becoming admin

On first run, a one-time claim token is printed to the console. Send it as a message to the Admin Group to become admin.

## Group management

| Command | Description |
|---------|-------------|
| `/create_group <name>` | Create a new group (you become its admin) |
| `/remove_group <address>` | Delete a group permanently |
| `/rename_group <address> <new_name>` | Rename a group |
| `/list_groups` | List all running groups |
| `/group_info <address>` | Show group details |

## Group admin management

| Command | Description |
|---------|-------------|
| `/assign_admin <group_address> <user_hash>` | Make a user admin of a group |
| `/remove_admin <group_address> <user_hash>` | Remove admin role from a user |

## Common commands

These are shared with normal groups:

| Command | Description |
|---------|-------------|
| `/help`, `/?` | Show available commands |
| `/info` | Show Admin Group name, address, member count |
| `/members` | List Admin Group members |
| `/admin <address>` | Add an admin to the Admin Group |
| `/kick <address>` | Remove a user from the Admin Group |
| `/name <new_name>` | Rename the Admin Group |
| `/leave` | Leave the Admin Group (admins cannot leave) |
