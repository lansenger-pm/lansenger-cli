# AGENTS.md — lansenger-cli

Python CLI for the Lansenger platform. Published to PyPI as `lansenger-cli`.

## How to run

- Install dev: `pip install -e ".[dev]"`
- Tests: `pytest -q`
- Build: `python -m build`
- Publish: push a git tag `vx.y.z` — CI (`.github/workflows/release.yml`) builds and uploads to PyPI automatically. Do NOT run `twine upload` manually; it conflicts with the CI publish step.

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

`pytest -q` MUST pass (0 failures) before pushing a release tag. The CI
Release workflow runs tests again and will block the upload on failure.
No exceptions.

### CI-driven publishing (do NOT publish manually)

Releases are published exclusively by the `Release` GitHub Actions workflow
on tag push (`v*`). The workflow verifies `pyproject.toml` matches the tag,
runs `pytest -q`, builds, and uploads to PyPI via OIDC trusted publishing.

**Do NOT run `twine upload` manually** — the package will already exist on
PyPI once the tag is pushed, so a manual upload will fail with
`400 File already exists` and leave a red CI run. To release: bump the
version in `pyproject.toml`, commit, then `git tag -a vx.y.z -m '...'` and
`git push origin vx.y.z`. If the CI publish fails for a non-duplicate reason,
fix the issue and re-run the failed workflow (do not re-push the same tag).

### Pass-through (external token) mode

The CLI's `get_client()` in `utils.py` supports `--app-token` external mode: when
`--app-token` is provided it creates a `LansengerSyncClient` with `app_id=""`,
`app_secret=""`, `app_token=<token>`, bypassing the credential store. This is the
LanMate/skill-suite usage pattern. Keep this path working — do not re-introduce a
required `app_id`/`app_secret` in the client construction.

## Current status

v0.12.0.
