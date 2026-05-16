# Running lxmf-group on NixOS

**Prerequisite:** rnsd must be running. lxmf-group does not start its own Reticulum instance — it connects to an existing rnsd process via `require_shared_instance=True`. Ensure rnsd is enabled and started before lxmf-group.

This project includes a `default.nix`. On NixOS you can fetch and import it directly.

Add the following to your `configuration.nix`:

```nix
{ pkgs, ... }:

let
  unstable = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {};
  lxmf-group = import (builtins.fetchTarball "https://codeberg.org/melsner/lxmf_group/archive/main.tar.gz") { pkgs = unstable; };
in
{
  users.users.lxmf-group = {
    isSystemUser = true;
    group = "lxmf-group";
  };

  users.groups.lxmf-group = {};

  systemd.services.lxmf-group = {
    description = "LXMF Distribution Group";
    after = [ "network.target" "rnsd.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      User = "lxmf-group";
      Group = "lxmf-group";
      WorkingDirectory = "/var/lib/lxmf-group";
      ExecStart = "${lxmf-group}/bin/lxmf-group --data /var/lib/lxmf-group/lxmf-group --rnsconfig /etc/reticulum";
      Restart = "on-failure";
      RestartSec = 5;
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "full";
      ProtectHome = true;
      ReadWritePaths = "/var/lib/lxmf-group";
      ProtectKernelTunables = true;
      ProtectKernelModules = true;
      ProtectControlGroups = true;
      RestrictNamespaces = true;
      LockPersonality = true;
      RestrictRealtime = true;
      RestrictSUIDSGID = true;
      PrivateDevices = false;
    };
  };
}
```

Rebuild:

```bash
sudo nixos-rebuild switch
```

On first start, the Admin Group is created and a one-time claim token is printed to the journal:

```bash
journalctl --unit lxmf-group --output=cat -n 30
```

Use `--output=cat` so the QR code ANSI colours are preserved and the code is scannable directly from the terminal.

Send the token to the Admin Group's LXMF address to become admin. Then use `/create_group <name>` to create groups.
