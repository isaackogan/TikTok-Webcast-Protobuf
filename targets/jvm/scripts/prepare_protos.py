"""Stage proto sources into build/proto-staging for Wire to consume.

Shared by both JVM modules (Java and Kotlin generation) — staged once at the JVM
root and read by each module's Wire task.

Two paths:

- **Legacy (v1, v2)**: merge all .proto files in the version into one synthetic
  `tiktok-schema.proto` with a single `package TikTok;` and inject
  `option java_package`. Necessary because v2 has cross-file type references
  without explicit `import` statements, which `protoc` tolerates when compiling
  multiple files at once but Wire rejects.

- **Modern (v3+)**: copy each file as-is and inject `option java_package` per
  file (preserving the proto's own `package`). Each file declares its own
  imports, so Wire is happy.

Output layout:
  build/proto-staging/v1/tiktok-schema.proto      (legacy: merged)
  build/proto-staging/v2/tiktok-schema.proto      (legacy: merged)
  build/proto-staging/v3/<original/relative/path>.proto  (modern: per-file)
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

# This script lives at targets/jvm/scripts/prepare_protos.py.
JVM_ROOT = Path(__file__).resolve().parent.parent
PROTO_ROOT = JVM_ROOT.parent.parent / "src" / "slim"
STAGING = JVM_ROOT / "build" / "proto-staging"

JAVA_GROUP = "com.eulerstream.webcast"
LEGACY_VERSIONS = {"v1", "v2"}
VERSION_DIR_RE = re.compile(r"^v\d+$")
SYNTAX_RE = re.compile(r'^syntax\s*=\s*"proto3";\s*$', re.MULTILINE)
PACKAGE_RE = re.compile(r'^package\s+([\w.]+)\s*;\s*$', re.MULTILINE)
JAVA_PKG_RE = re.compile(r'^option\s+java_package\s*=', re.MULTILINE)
HEADER_LINE_RE = re.compile(r"^\s*(syntax|import|package)\b")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def java_package_for(version: str, proto_pkg: str | None) -> str:
    if version in LEGACY_VERSIONS or not proto_pkg:
        return f"{JAVA_GROUP}.{version}"
    return f"{JAVA_GROUP}.{version}.{proto_pkg}"


def strip_header_lines(content: str) -> str:
    content = BLOCK_COMMENT_RE.sub("", content)
    out: list[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if HEADER_LINE_RE.match(line) or stripped.startswith("//"):
            continue
        out.append(line.split("//", 1)[0].rstrip())
    return "\n".join(out).strip()


def write_legacy_merged(version: str, version_dir: Path) -> int:
    protos = sorted(p for p in version_dir.rglob("*.proto") if p.is_file())
    if not protos:
        raise SystemExit(f"No .proto files under {version_dir}")
    merged_body = "\n\n".join(strip_header_lines(p.read_text(encoding="utf8")) for p in protos)
    java_pkg = java_package_for(version, None)
    out = (
        'syntax = "proto3";\n'
        f'package webcast.{version};\n'
        f'option java_package = "{java_pkg}";\n\n'
        f"{merged_body}\n"
    )
    dst_dir = STAGING / version
    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / f"tiktok-schema-{version}.proto").write_text(out, encoding="utf8")
    return len(protos)


def write_modern(version: str, version_dir: Path) -> int:
    count = 0
    for proto in sorted(version_dir.rglob("*.proto")):
        text = proto.read_text(encoding="utf8")
        proto_pkg_match = PACKAGE_RE.search(text)
        proto_pkg = proto_pkg_match.group(1) if proto_pkg_match else None
        java_pkg = java_package_for(version, proto_pkg)
        if not JAVA_PKG_RE.search(text):
            option = f'\noption java_package = "{java_pkg}";\n'
            if SYNTAX_RE.search(text):
                text = SYNTAX_RE.sub(lambda m: m.group(0) + option, text, count=1)
            else:
                text = f'syntax = "proto3";\n{option}\n{text}'

        rel = proto.relative_to(version_dir)
        dst = STAGING / version / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf8")
        count += 1
    return count


def main() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)

    versions = sorted(
        entry for entry in PROTO_ROOT.iterdir()
        if entry.is_dir() and VERSION_DIR_RE.match(entry.name)
    )
    if not versions:
        raise SystemExit(f"No version directories found under {PROTO_ROOT}")

    total = 0
    for version_dir in versions:
        version = version_dir.name
        if version in LEGACY_VERSIONS:
            count = write_legacy_merged(version, version_dir)
            print(f"[{version}] merged {count} files into tiktok-schema.proto")
        else:
            count = write_modern(version, version_dir)
            print(f"[{version}] staged {count} files (modern)")
        total += count

    print(f"Done. {total} protos processed → {STAGING}")


if __name__ == "__main__":
    main()
