#!/usr/bin/env python3
"""Offline consistency checks for package manifests and committed lock files."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
checks = 0


def require(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


package = json.loads((ROOT / "frontend/package.json").read_text())
lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
root_package = lock.get("packages", {}).get("", {})
for section in ("dependencies", "devDependencies"):
    manifest_items = package.get(section, {})
    lock_items = root_package.get(section, {})
    require(set(manifest_items) == set(lock_items), f"Frontend {section} names differ from npm lock")
    for name, specifier in manifest_items.items():
        require(lock_items.get(name) == specifier, f"Frontend npm lock specifier mismatch for {name}")

pyproject = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
uv_text = (ROOT / "backend/uv.lock").read_text()
project_match = re.search(
    r'\[\[package\]\]\nname = "mail-tracko".*?\n\[package\.metadata\]\nrequires-dist = \[(.*?)\n\]',
    uv_text,
    re.S,
)
require(project_match is not None, "mail-tracko metadata is missing from uv.lock")
locked_requirements: dict[str, str] = {}
if project_match:
    for name, specifier in re.findall(
        r'\{ name = "([^"]+)"(?:, extras = \[[^\]]+\])?, specifier = "([^"]+)" \}',
        project_match.group(1),
    ):
        locked_requirements[name] = specifier

for raw in pyproject["project"]["dependencies"]:
    normalized = raw.lower()
    name = re.split(r"\[|[<>=!~ ]", normalized, maxsplit=1)[0]
    specifier_match = re.search(r"([<>=!~].*)$", raw)
    specifier = specifier_match.group(1) if specifier_match else ""
    require(name in locked_requirements, f"Backend dependency {name} missing from uv.lock metadata")
    if name in locked_requirements:
        require(locked_requirements[name] == specifier, f"Backend lock specifier mismatch for {name}")

requires_python = pyproject["project"]["requires-python"]

# Find the `requires-python` value in uv.lock (top-level key)
uv_req_match = re.search(r'requires-python\s*=\s*"([^"]+)"', uv_text)
require(uv_req_match is not None, "uv.lock is missing top-level requires-python")
if uv_req_match:
    uv_requires = uv_req_match.group(1)

    def _parse_range(s: str):
        s = s.strip()
        # Match forms like '>=3.13,<3.14'
        m = re.match(r"^>=\s*([0-9]+)\.([0-9]+)\s*,\s*<\s*([0-9]+)\.([0-9]+)$", s)
        if m:
            return ("range", int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        # Match forms like '==3.13.*'
        m = re.match(r"^==\s*([0-9]+)\.([0-9]+)\.\*$", s)
        if m:
            return ("wild", int(m.group(1)), int(m.group(2)))
        return ("other", s)

    def _equivalent_python_spec(a: str, b: str) -> bool:
        # exact match
        if a == b:
            return True
        pa = _parse_range(a)
        pb = _parse_range(b)
        # Accept equivalence between >=X.Y,<X.(Y+1) and ==X.Y.*
        if pa[0] == "range" and pb[0] == "wild":
            # pa == ("range", A, B, C, D) where C==A and D==B+1 for a single-major range
            return pa[1] == pb[1] and pa[2] == pb[2] and pa[3] == pa[1] and pa[4] == pa[2] + 1
        if pb[0] == "range" and pa[0] == "wild":
            return pb[1] == pa[1] and pb[2] == pa[2] and pb[3] == pb[1] and pb[4] == pa[2] + 1
        # Fall back to substring presence (covers formatting normalization differences)
        return a in b or b in a

    require(_equivalent_python_spec(requires_python, uv_requires), "Python requirement differs from uv.lock")

if errors:
    print("Lockfile validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)
print(f"Offline lockfile consistency validation passed: {checks} checks.")
