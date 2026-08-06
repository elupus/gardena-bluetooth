# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What this is

A Python library (`gardena_bluetooth`) for communicating with Gardena Bluetooth watering devices (valves, water computers, pumps) over BLE. It defines the known GATT services/characteristics and parsers for them, and is primarily consumed by Home Assistant.

## Commands

Uses `uv` for dependency management.

```bash
uv sync                    # install dependencies
uv run pytest -sxv         # run tests
uv run ruff check .        # lint
uv run ruff check --fix .  # lint with autofix
uv run ruff format .       # format
```

Tests are fully mocked (BLE connections are patched) — no real hardware or adapter is needed to run the suite.

## Code style

- Ruff handles both linting and import sorting (`I` rules enabled) and formatting — run it rather than hand-formatting imports.
- Services and characteristics in `gardena_bluetooth/const.py` are declared as class attributes using `Characteristic*` descriptors from `gardena_bluetooth/parse.py`, keyed by BLE UUID. Follow this existing declarative pattern when adding new services/characteristics rather than writing bespoke parsing code.
- Inline code comments should be kept to minimum and preferably moved to function level.

## Conventions

- Commit messages follow Conventional Commits style (`feat:`, `fix:`, `chore:`, etc.) — see `git log` for examples.
- PRs are squash-merged normally, but can be rebase merged with clean series.
