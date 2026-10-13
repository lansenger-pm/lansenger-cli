#!/usr/bin/env python3
"""Credential scanner (metadata-level, Harness ⑤验证层).

Discipline (from Harness Bootstrap Playbook v3):
- Output ONLY `file:line:key` (default) or `path|key|count` (--ratchet).
- NEVER print, log, or echo any credential value.
- Key set = minimal reference set; single word `key` excluded (too noisy).
- Does not scan its own control plane: harness/, evals/, templates/,
  scripts/hooks/, this file, scripts/verify.sh, root AGENTS/KNOWLEDGE.
- Security gate (commit-blocking detectors, same FAIL path as secrets):
  internal test-environment hosts / high-entropy hex (>=32) / local known-value
  blocklist (harness/security-blocklist.local, gitignored, never committed).

Exit codes: 0 = scan ran (findings reported via stdout, judgement left to
verify.sh against the allowlist); 2 = scanner itself failed.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

KEY_PATTERN = r"(?:password|passwd|secret|token|credential|api_?key|private_?key|keystore)"
KEY_START = r"(?<![A-Za-z0-9])"
# R1: key assignment to a quoted string of >= 8 chars  ->  key: "value"
R1 = re.compile(rf"{KEY_START}({KEY_PATTERN}\w*)\s*[:=]\s*[\"']([^\"']{{8,}})[\"']", re.IGNORECASE)
# R2: raw unquoted env-style assignment (no spaces, >= 20 chars)  ->  KEY=value
R2 = re.compile(rf"{KEY_START}({KEY_PATTERN}\w*)\s*=\s*([A-Za-z0-9_\-+/=.{{}}]{{20,}})", re.IGNORECASE)
# Placeholder-value filter (metadata-level, values themselves are never stored/logged):
# uppercase placeholders (YOUR_APP_SECRET), placeholder word combos (your-secret-123),
# template markers (<...>/{...}) and pure lowercase dotted identifiers are NOT
# credential-shaped. Anything else (e.g. mixed-entropy fakes) stays reportable so
# the allowlist ratchet keeps count of fixture fakes and real secrets cannot
# blend in unnoticed.
def is_placeholder(value: str) -> bool:
    if re.fullmatch(r"[A-Z0-9_]+", value):
        return True
    if re.fullmatch(r"(your|my|xxx+|example|sample|demo|dummy|fake|placeholder|test)[-_a-zA-Z0-9]*", value, re.IGNORECASE):
        return True
    if re.fullmatch(r"[a-z_.]+", value):
        return True
    if "<" in value or "{" in value:
        return True
    return False
# R3: PEM / private key block marker
R3 = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")

# --- security-gate detectors (see module docstring) ---
INTERNAL_ENDPOINT_RES = [
    re.compile(r"(?:open|user)-[a-z0-9-]+\.(?:e|t)\.lanxin\.cn"),
]
LONG_HEX = re.compile(r"[0-9a-fA-F]{32,}")
BLOCKLIST_PATH = REPO / "harness" / "security-blocklist.local"


def load_blocklist() -> list[str]:
    """Read the local (gitignored) known-value blocklist; absent file = empty."""
    if not BLOCKLIST_PATH.exists():
        return []
    try:
        lines = BLOCKLIST_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]

SCAN_ROOTS = [
    "src",
    "tests",
    "docs",
    "scripts",
    ".github",
    "pyproject.toml",
    "CHANGELOG.md",
]
SCAN_GLOBS = ["README*.md"]

EXCLUDED_PARTS = {
    "harness",
    "evals",
    "templates",
    "hooks",
    ".git",
    ".venv",
    ".qagent",
    ".agents",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}
EXCLUDED_FILES = {"scan_secrets.py", "verify.sh", "uv.lock", "KNOWLEDGE.md"}
MAX_FILE_BYTES = 1_000_000


def iter_targets() -> list[Path]:
    targets: list[Path] = []
    for root in SCAN_ROOTS:
        p = REPO / root
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if not f.is_file():
                    continue
                if any(part in EXCLUDED_PARTS for part in f.parts):
                    continue
                if f.name in EXCLUDED_FILES or any(p.endswith(".egg-info") for p in f.parts):
                    continue
                targets.append(f)
    for pat in SCAN_GLOBS:
        targets.extend(sorted(REPO.glob(pat)))
    seen, out = set(), []
    for t in targets:
        rp = t.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(t)
    return out


def scan_line(line: str, blocklist: list[str] = ()) -> list[str]:
    keys: list[str] = []
    m = R3.search(line)
    if m:
        keys.append("private-key-block")
        return keys
    for m in R1.finditer(line):
        if not is_placeholder(m.group(2)):
            keys.append(m.group(1))
    for m in R2.finditer(line):
        if not is_placeholder(m.group(2)):
            keys.append(m.group(1))
    for pattern in INTERNAL_ENDPOINT_RES:
        if pattern.search(line):
            keys.append("internal-endpoint")
            break
    if LONG_HEX.search(line):
        keys.append("long-hex-value")
    for fragment in blocklist:
        if fragment in line:
            keys.append("blocklisted-value")
            break
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ratchet",
        action="store_true",
        help="emit `path|key|count` lines (for allowlist comparison)",
    )
    args = parser.parse_args()

    findings: list[tuple[str, int, str]] = []
    scanned = 0
    blocklist = load_blocklist()
    for path in iter_targets():
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, IsADirectoryError, PermissionError, OSError):
            continue
        scanned += 1
        rel = path.relative_to(REPO).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            for key in scan_line(line, blocklist):
                findings.append((rel, lineno, key))

    if args.ratchet:
        agg: Counter[tuple[str, str]] = Counter()
        for rel, _lineno, key in findings:
            agg[(rel, key)] += 1
        for (rel, key), count in sorted(agg.items()):
            print(f"{rel}|{key}|{count}")
    else:
        for rel, lineno, key in sorted(findings):
            print(f"{rel}:{lineno}:{key}")
        if not findings:
            print("# no credential-shaped hits (values are never read or shown)")
    print(f"# scanned {scanned} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
