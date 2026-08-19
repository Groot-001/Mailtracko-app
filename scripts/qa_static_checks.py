"""Dependency-free source integrity checks for MailTracko.

Run from the repository root:
    python scripts/qa_static_checks.py
"""
from __future__ import annotations

import ast
import compileall
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "src"
TESTS = ROOT / "backend" / "tests"

EXCLUDED_PARTS = {"node_modules", ".venv", ".git"}
MICROSOFT_PATTERN = re.compile(
    r"microsoft|outlook|office\s*365|azure|m365|hotmail|live\.com|msal",
    re.IGNORECASE,
)
REL_IMPORT_PATTERN = re.compile(
    r'''(?:from\s+|import\s*\(|import\s+)["'](\.{1,2}/[^"']+)["']'''
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def text_files() -> list[Path]:
    extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".html", ".yml", ".yaml"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if EXCLUDED_PARTS.intersection(path.parts):
            continue
        files.append(path)
    return files




def check_text_integrity(files: list[Path]) -> None:
    nul_offenders: list[Path] = []
    decode_offenders: list[Path] = []
    for path in files:
        raw = path.read_bytes()
        if b"\x00" in raw:
            nul_offenders.append(path)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            decode_offenders.append(path)
    if nul_offenders:
        fail("NUL-byte corruption found in: " + ", ".join(str(p.relative_to(ROOT)) for p in nul_offenders))
    if decode_offenders:
        fail("Non-UTF-8 source/config text found in: " + ", ".join(str(p.relative_to(ROOT)) for p in decode_offenders))
    print("PASS: no NUL-byte or UTF-8 source corruption")

def check_no_bom(files: list[Path]) -> None:
    offenders = [path for path in files if path.read_bytes().startswith(b"\xef\xbb\xbf")]
    if offenders:
        fail("UTF-8 BOM found in: " + ", ".join(str(p.relative_to(ROOT)) for p in offenders))
    print("PASS: no UTF-8 BOM in source files")


def check_no_microsoft(files: list[Path]) -> None:
    """Scan executable/config product surfaces, not QA reports that document removal."""
    hits: list[str] = []
    product_roots = (FRONTEND, BACKEND, ROOT / "docker-compose.yml", ROOT / ".env.integration.example")
    candidates: list[Path] = []
    for item in product_roots:
        if item.is_file():
            candidates.append(item)
        elif item.exists():
            candidates.extend(path for path in item.rglob("*") if path.is_file())

    for path in candidates:
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".html", ".yml", ".yaml", ".env", ".example", ".json"}:
            continue
        if EXCLUDED_PARTS.intersection(path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(content.splitlines(), start=1):
            if MICROSOFT_PATTERN.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    if hits:
        fail("Microsoft-related executable/config residue found:\n" + "\n".join(hits[:50]))
    print("PASS: no Microsoft/Outlook/Office365 executable/config residue")


def check_python() -> None:
    if not compileall.compile_dir(str(BACKEND), quiet=1):
        fail("backend source compile failed")
    if not compileall.compile_dir(str(TESTS), quiet=1):
        fail("backend tests compile failed")

    for path in list(BACKEND.rglob("*.py")) + list(TESTS.rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("PASS: backend Python syntax/AST")


def check_python_local_imports() -> None:
    missing: list[str] = []
    for path in list(BACKEND.rglob("*.py")) + list(TESTS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                if module != "src" and not module.startswith("src."):
                    continue
                candidate = BACKEND.joinpath(*module.split(".")[1:])
                if not (
                    candidate.is_dir()
                    or candidate.with_suffix(".py").exists()
                    or (candidate / "__init__.py").exists()
                ):
                    missing.append(f"{path.relative_to(ROOT)} -> {module}")
    if missing:
        fail("missing local Python imports:\n" + "\n".join(missing[:50]))
    print("PASS: local Python import paths")


def check_frontend_relative_imports() -> None:
    missing: list[str] = []
    files = list(FRONTEND.rglob("*.ts")) + list(FRONTEND.rglob("*.tsx"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for specifier in REL_IMPORT_PATTERN.findall(text):
            base = path.parent / specifier
            candidates = [
                base,
                Path(str(base) + ".ts"),
                Path(str(base) + ".tsx"),
                Path(str(base) + ".js"),
                Path(str(base) + ".jsx"),
                base / "index.ts",
                base / "index.tsx",
                base / "index.js",
                base / "index.jsx",
            ]
            if not any(candidate.exists() for candidate in candidates):
                missing.append(f"{path.relative_to(ROOT)} -> {specifier}")
    if missing:
        fail("missing relative frontend imports:\n" + "\n".join(missing[:50]))
    print(f"PASS: relative frontend imports ({len(files)} TS/TSX files)")



def check_confirmed_qa_regressions() -> None:
    campaign_api = (ROOT / "frontend/src/feature/campaigns/api/campaignApi.ts").read_text(encoding="utf-8")
    campaign_dashboard = (ROOT / "frontend/src/feature/campaigns/components/CampaignDashboard.tsx").read_text(encoding="utf-8")
    campaign_router = (ROOT / "backend/src/modules/campaign/presentation/routers/campaign_routers.py").read_text(encoding="utf-8")
    contacts_dashboard = (ROOT / "frontend/src/feature/contacts/components/ContactsDashboard.tsx").read_text(encoding="utf-8")
    index_html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")

    if "include_archived: params.include_archived ?? false" not in campaign_api:
        fail("campaign list API must exclude soft-deleted campaigns by default")
    if "include_archived: false" not in campaign_dashboard:
        fail("campaign dashboard must request only non-deleted campaigns")
    if "window.confirm(" in campaign_dashboard:
        fail("campaign deletion must use the app confirmation UI, not window.confirm")
    if "or (status is not None and status == CampaignStatus.ARCHIVED)" in campaign_router:
        fail("archived status filtering must not implicitly include soft-deleted campaigns")
    if "lists[0]?.uuid" in contacts_dashboard:
        fail("contact creation must not silently select the first contact list")
    if '<title>MailTracko</title>' not in index_html:
        fail("frontend browser title must be MailTracko")
    if "lg:sticky lg:top-6 lg:self-start" not in contacts_dashboard:
        fail("contacts Quick Actions must remain sticky on desktop")
    if 'maxLength={50}' not in contacts_dashboard:
        fail("collection name input must enforce the project-wide 50-character limit")
    if "truncate font-medium" not in contacts_dashboard and "break-words font-medium" not in contacts_dashboard:
        fail("collection names must truncate or wrap long text without breaking the layout")
    if "line-clamp-2 break-words" not in contacts_dashboard and "break-words text-xs" not in contacts_dashboard:
        fail("collection descriptions must clamp or wrap long text without breaking the layout")

    print("PASS: confirmed QA frontend regressions")

def main() -> int:
    files = text_files()
    check_text_integrity(files)
    check_no_bom(files)
    check_no_microsoft(files)
    check_python()
    check_python_local_imports()
    check_frontend_relative_imports()
    check_confirmed_qa_regressions()
    print("ALL STATIC QA CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
