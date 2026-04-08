# Development

## Prerequisites

[Nix](https://nixos.org/) is used to provide a reproducible development shell.

## Getting started

```bash
nix-shell
make venv
source .venv/bin/activate
make install
```

## Running tests

```bash
make test
```

## Building

```bash
make build
```

## Building with Nix

```bash
nix-build
./result/bin/lxmf-group --help
```

## Bumping the version

Uses [bump-my-version](https://github.com/callowayproject/bump-my-version):

```bash
bump-my-version bump patch   # 0.1.0 → 0.1.1
bump-my-version bump minor   # 0.1.0 → 0.2.0
bump-my-version bump major   # 0.1.0 → 1.0.0
```
