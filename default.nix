{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3;
  versionFile = builtins.readFile ./lxmf_group/_version.py;
  version = builtins.head (builtins.match ''.*__version__ = "([^"]+)".*'' versionFile);

  lxmfy = python.pkgs.buildPythonPackage {
    pname = "lxmfy";
    version = "1.6.1";
    src = pkgs.fetchgit {
      url = "https://git.quad4.io/LXMFy/LXMFy.git";
      rev = "36e2b5c9210703b9cfd7867ddacda991574c53dc";
      hash = "sha256-jEjvogqXoKTH5UbPFfgZsk5WnOYvwPY89itDFeO4LZ8=";
    };
    format = "pyproject";
    build-system = [ python.pkgs.poetry-core ];
    dependencies = with python.pkgs; [ rns lxmf ];
    pythonRelaxDeps = [ "rns" ];
  };
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
    lxmfy
    platformdirs
    qrcode
    msgpack
  ];

  meta = {
    description = "Server-Side group functions for LXMF based apps";
    license = pkgs.lib.licenses.mit;
  };
}
