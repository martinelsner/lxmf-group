# Family group

A simple private group where members can only be added by admin invitation.

## Setup

```bash
lxmf-group
```

On first run, the Admin Group is created and a claim token is printed. Send it to the Admin Group to become admin.

Then create the family group:

```text
/create_group Family
```

The group is private by default. Group admins can make it public with `/public`.

## Adding members

From inside the family group:

```text
/add <member_lxmf_address>
```

## Removing members

```text
/kick <member_lxmf_address>
```
