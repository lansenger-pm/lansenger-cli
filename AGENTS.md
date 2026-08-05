# AGENTS.md — lansenger-cli

Python CLI for the Lansenger platform. Published to PyPI as `lansenger-cli`.

## How to run

- Install dev: `pip install -e ".[dev]"`
- Tests: `pytest -q`
- Build: `python -m build`
- Publish: `python -m twine upload dist/lansenger_cli-<version>*`

## Tech stack

Python 3.10+, typer (CLI framework), rich (output), httpx. Depends on `lansenger-sdk`.

## Layout

- `src/lansenger_cli/` — CLI source (commands, utils)
- `tests/` — pytest suite
- `pyproject.toml` — version + packaging

## Release rules — CRITICAL

### Version number

Lives in ONE place: `pyproject.toml` (`version = "x.y.z"`). The tag name must match
(`vx.y.z`). PyPI does not allow re-uploading a version — bump to the next patch if
a release was published with a mistake.

### NEVER publish without a full green test run

`pytest -q` MUST pass (0 failures) before `twine upload` / pushing a release tag.
No exceptions.

### Pass-through (external token) mode

The CLI's `get_client()` in `utils.py` supports `--app-token` external mode: when
`--app-token` is provided it creates a `LansengerSyncClient` with `app_id=""`,
`app_secret=""`, `app_token=<token>`, bypassing the credential store. This is the
LanMate/skill-suite usage pattern. Keep this path working — do not re-introduce a
required `app_id`/`app_secret` in the client construction.

## Current status

v0.11.0. No CI incidents.
