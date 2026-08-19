"""
Project setup script.

Usage:
    uv run python scripts/setup/project_setup.py

Prompts for a project name and updates all project-wide references.
Creates .env / .env.local / .env.test from .example.env if missing...
"""

import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_DIR = BASE_DIR / "env"
EXAMPLE_ENV = ENV_DIR / ".example.env"

FILES_TO_UPDATE = {
    "Makefile": [
        (r"^PROJECT_NAME \?= .+", "PROJECT_NAME ?= {name}", re.MULTILINE),
    ],
    "pyproject.toml": [
        (r'^name = .+', 'name = "{name}"', re.MULTILINE),
    ],
    "src/core/config/settings.py": [
        (
            r"^    PROJECT_NAME: str = .+",
            '    PROJECT_NAME: str = "{name}"',
            re.MULTILINE,
        ),
    ],
}


def _slugify(name: str) -> str:
    name = name.lower().strip().replace(" ", "-")
    name = re.sub(r"[^a-z0-9_-]", "", name)
    name = re.sub(r"^[^a-z0-9]+", "", name)
    return name


def prompt_project_name() -> str:
    name = input("Enter project name: ").strip()
    if not name:
        print("Project name cannot be empty.")
        raise SystemExit(1)

    slug = _slugify(name)
    if slug != name:
        print(
            f'Project name will be normalized to: "{slug}" '
            "(Docker requires lowercase alphanumeric, hyphens, and underscores)"
        )
        name = slug
    return name


def update_file(filepath: Path, name: str, patterns: list):
    if not filepath.exists():
        print(f"  [SKIP] {filepath.relative_to(BASE_DIR)} — not found")
        return

    content = filepath.read_text(encoding="utf-8")
    new_content = content
    for item in patterns:
        pattern, template, *flags = item
        replacement = template.format(name=name)
        flag = flags[0] if flags else 0
        new_content, count = re.subn(pattern, replacement, new_content, flags=flag)
        if count == 0:
            print(
                f"  [WARN] No match for {pattern!r} in {filepath.relative_to(BASE_DIR)}"
            )
        else:
            print(f"  [OK]   {count} replacement(s) for {pattern!r}")

    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  [SAVE] {filepath.relative_to(BASE_DIR)}")


def create_env_file(filename: str, name: str):
    filepath = ENV_DIR / filename
    if filepath.exists():
        print(f"  [SKIP] {filepath.relative_to(BASE_DIR)} — already exists")
        return

    if not EXAMPLE_ENV.exists():
        print(
            f"  [SKIP] {filepath.relative_to(BASE_DIR)} — {EXAMPLE_ENV.relative_to(BASE_DIR)} not found"
        )
        return

    shutil.copy2(EXAMPLE_ENV, filepath)
    content = filepath.read_text(encoding="utf-8")
    content = content.replace("PROJECT_NAME=your project name", f"PROJECT_NAME={name}")
    filepath.write_text(content, encoding="utf-8")
    print(f"  [CREATE] {filepath.relative_to(BASE_DIR)}")


def main():
    name = prompt_project_name()
    print(f"\nUpdating project name to: {name}\n")

    print("Updating source files ...")
    for rel_path, patterns in FILES_TO_UPDATE.items():
        abspath = BASE_DIR / rel_path
        update_file(abspath, name, patterns)

    print("\nCreating env files (if missing) ...")
    for filename in (".env", ".env.local", ".env.test"):
        create_env_file(filename, name)

    print("\nDone.")


if __name__ == "__main__":
    main()
