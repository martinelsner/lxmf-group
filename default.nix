{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  versionFile = builtins.readFile ./lxmf_group/_version.py;
  version = builtins.head (builtins.match ''.*__version__ = "([^"]+)".*'' versionFile);
in
python.pkgs.buildPythonApplication {
  pname = "lxmf-group";
  inherit version;
  src = pkgs.lib.cleanSource ./.;
  format = "pyproject";

  build-system = [ python.pkgs.hatchling ];

  dependencies = with python.pkgs; [
    rns
    lxmf
    platformdirs
    qrcode
  ];

  meta = {
    description = "Server-Side group functions for LXMF based apps";
    license = pkgs.lib.licenses.mit;
  };
}
