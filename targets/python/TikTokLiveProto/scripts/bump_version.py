from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r'(?m)^version = "(\d+)\.(\d+)\.(\d+)"$')


def bump(version: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if part == "patch":
        return major, minor, patch + 1
    if part == "minor":
        return major, minor + 1, 0
    if part == "major":
        return major + 1, 0, 0
    raise ValueError(f"Unsupported bump type: {part}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/bump_version.py <patch|minor|major>")

    bump_type = sys.argv[1]
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = pyproject.read_text(encoding="utf8")
    match = VERSION_RE.search(content)
    if match is None:
        raise RuntimeError("Could not find project version in pyproject.toml")

    current = tuple(int(part) for part in match.groups())
    next_version = ".".join(str(part) for part in bump(current, bump_type))
    updated = VERSION_RE.sub(f'version = "{next_version}"', content, count=1)
    pyproject.write_text(updated, encoding="utf8")
    print(next_version)


if __name__ == "__main__":
    main()
