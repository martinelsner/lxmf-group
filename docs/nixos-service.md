# Running lxmf-group on NixOS

This project includes a `default.nix`. On NixOS you can fetch and import it directly.

Add the following to your `configuration.nix`:

```nix
{ pkgs, ... }:

let
  unstable = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {};
  lxmf-group = import (builtins.fetchTarball "https://codeberg.org/melsner/lxmf_group/archive/main.tar.gz") { pkgs = unstable; };
in
{
  users.users.reticulum = {
    isSystemUser = true;
    group = "reticulum";
    home = "/var/lib/reticulum";
    createHome = true;
  };

  users.groups.reticulum = {};

  systemd.services.lxmf-group = {
    description = "LXMF Distribution Group";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      User = "reticulum";
      Group = "reticulum";
      WorkingDirectory = "/var/lib/reticulum";
      ExecStart = "${lxmf-group}/bin/lxmf-group --data /var/lib/reticulum/lxmf-group";
      Restart = "on-failure";
      RestartSec = 5;
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "full";
      ProtectHome = true;
      ReadWritePaths = "/var/lib/reticulum";
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
journalctl --unit lxmf-group -n 30
```

Send the token to the Admin Group's LXMF address to become admin. Then use `/create_group <name>` to create groups.
