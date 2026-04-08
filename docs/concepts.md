# Concepts

## What is a group?

A group is an LXMF distribution endpoint hosted by the lxmf-group server. A single server process can host multiple independent groups, each with its own identity and members. It receives messages from members and forwards them to every other member — like a mailing list with chat features. Any LXMF-compatible client (Sideband, NomadNet, Columba, ...) can talk to it because each group behaves like a regular LXMF endpoint.

## Architecture

The server runs two kinds of bots, both built on LXMFy:

- **Admin Group** — a single server-level bot for managing groups (create, remove, rename, assign admins). Only Admin Group members can use it.
- **Groups** — one bot per group, handling message relay and group-level commands.

Each bot has its own LXMF identity and address.

## Roles

Membership and permissions are managed through LXMFy's role system. There are two roles:

| Role | Purpose |
|------|---------|
| **admin** | Full control. Can invite/kick users, promote admins, rename the group, change visibility, delete the group. |
| **user** | Can send and receive messages, view group info and members, leave the group. |

A member is anyone who has been assigned a role. An admin is anyone with the `admin` role.

## Public vs private groups

New groups start as private. Group admins can change this with `/public` and `/private`.

- **Public** — anyone can join by sending a message. They are automatically added as a user.
- **Private** — only invited users can participate. Unknown senders get a rejection message.

## How messages are transported

```text
Client A ──LXMF──> Group Bot ──LXMF──> Client B
                              ──LXMF──> Client C
```

All messages are standard encrypted 1:1 LXMF messages. The group bot redistributes what it receives.

## Command interface

Commands start with `/` (e.g. `/help`, `/invite <address>`). Any message that does not start with `/` is treated as a normal group message and relayed to all members.

Type `/help` or `/?` to see available commands. For a full reference, see [Group commands](group-commands.md) and [Admin Group commands](admin-group-commands.md).
