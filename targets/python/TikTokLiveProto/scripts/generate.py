from __future__ import annotations

import re
import shutil
import subprocess
import sysconfig
from pathlib import Path
from shutil import which
from site import getuserbase

PKG_ROOT = Path(__file__).resolve().parent.parent
PROTO_ROOT = PKG_ROOT.parent.parent.parent / "src" / "slim"
TMP_DIR = PKG_ROOT / "tmp"
SRC_PKG = PKG_ROOT / "src" / "TikTokLiveProto"

# v1 & v2 use the legacy "merge into a single header-less proto" path so that
# betterproto2 emits a flat module per version. v3+ keeps the original package
# + directory structure since multi-package schemas can't be merged.
LEGACY_VERSIONS = {"v1", "v2"}

HEADER = 'syntax = "proto3";\n\n'
VERSION_DIR_RE = re.compile(r"^v\d+$")
HEADER_LINE_RE = re.compile(r"^\s*(syntax|import|package)\b")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
PYDANTIC_FORBID_CONFIG = ', config={"extra": "forbid"}'
BETTERPROTO_OPTS = "pydantic_dataclasses,client_generation=none"


def list_protos(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.proto") if path.is_file())


def strip_header_lines(content: str) -> str:
    content = BLOCK_COMMENT_RE.sub("", content)
    out_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if HEADER_LINE_RE.match(line) or stripped.startswith("//"):
            continue
        out_lines.append(line.split("//", 1)[0].rstrip())
    return "\n".join(out_lines).strip()


def resolve_plugin() -> Path:
    env_path = which("protoc-gen-python_betterproto2")
    if env_path:
        return Path(env_path)

    candidates = [
        Path(sysconfig.get_path("scripts") or "") / "protoc-gen-python_betterproto2",
        Path(getuserbase()) / "bin" / "protoc-gen-python_betterproto2",
        PKG_ROOT / ".venv" / "bin" / "protoc-gen-python_betterproto2",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "protoc-gen-python_betterproto2 not found. "
        "Install it with `pip install \"betterproto2_compiler>=0.9,<0.10\"`."
    )


def merge_version(version: str) -> tuple[Path, Path]:
    src_dir = PROTO_ROOT / version
    protos = list_protos(src_dir)
    if not protos:
        raise FileNotFoundError(f"No .proto files under {src_dir}")

    merged = HEADER + "\n\n".join(
        strip_header_lines(path.read_text(encoding="utf8")) for path in protos
    ) + "\n"

    out_dir = TMP_DIR / "proto" / version
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"tiktok-schema-{version}.proto"
    out_file.write_text(merged, encoding="utf8")
    return out_dir, out_file


def extract_legacy_package(tmp_out: Path, out_gen: Path) -> None:
    generated_file = tmp_out / "__init__.py"
    if not generated_file.exists():
        raise RuntimeError(f"Expected betterproto2 to emit {generated_file}")

    shutil.rmtree(out_gen, ignore_errors=True)
    out_gen.mkdir(parents=True, exist_ok=True)
    for child in tmp_out.iterdir():
        if child.name == "py.typed":
            continue
        shutil.move(str(child), out_gen / child.name)

    init_file = out_gen / "__init__.py"
    init_text = init_file.read_text(encoding="utf8")
    init_file.write_text(
        init_text.replace(PYDANTIC_FORBID_CONFIG, ""),
        encoding="utf8",
    )


def generate_legacy(version: str, plugin_path: Path) -> None:
    """Merge all .proto files into one synthetic schema, emit flat module."""
    proto_dir, proto_file = merge_version(version)
    tmp_out = TMP_DIR / "compiled" / version
    out_gen = SRC_PKG / version
    shutil.rmtree(tmp_out, ignore_errors=True)
    tmp_out.mkdir(parents=True, exist_ok=True)

    cmd = [
        "protoc",
        f"--plugin=protoc-gen-python_betterproto2={plugin_path}",
        f"-I={proto_dir}",
        f"--python_betterproto2_out={tmp_out}",
        f"--python_betterproto2_opt={BETTERPROTO_OPTS}",
        str(proto_file),
    ]

    print(f"[{version}] protoc + betterproto2 (legacy) ...")
    subprocess.run(cmd, check=True)
    extract_legacy_package(tmp_out, out_gen)


def generate_modern(version: str, plugin_path: Path) -> None:
    """Run betterproto2 against the version dir directly, preserving package + dir layout."""
    version_dir = PROTO_ROOT / version
    protos = list_protos(version_dir)
    if not protos:
        raise FileNotFoundError(f"No .proto files under {version_dir}")

    out_gen = SRC_PKG / version
    shutil.rmtree(out_gen, ignore_errors=True)
    out_gen.mkdir(parents=True, exist_ok=True)

    cmd = [
        "protoc",
        f"--plugin=protoc-gen-python_betterproto2={plugin_path}",
        f"-I={version_dir}",
        f"--python_betterproto2_out={out_gen}",
        f"--python_betterproto2_opt={BETTERPROTO_OPTS}",
        *(str(p) for p in protos),
    ]

    print(f"[{version}] protoc + betterproto2 (modern, {len(protos)} files) ...")
    subprocess.run(cmd, check=True)


def write_package_files(versions: list[str]) -> None:
    SRC_PKG.mkdir(parents=True, exist_ok=True)
    (SRC_PKG / "__init__.py").write_text(
        '"""Python betterproto2 bindings for the TikTok Webcast protobuf schema."""\n\n'
        "__all__ = [\n"
        + "".join(f'    "{version}",\n' for version in versions)
        + "]\n",
        encoding="utf8",
    )
    (SRC_PKG / "py.typed").touch()


def clean_previous_outputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    shutil.rmtree(SRC_PKG / "generated", ignore_errors=True)
    shutil.rmtree(PKG_ROOT / "src" / "tiktok_live_proto", ignore_errors=True)

    if not SRC_PKG.exists():
        return

    for child in SRC_PKG.iterdir():
        if child.is_dir() and VERSION_DIR_RE.match(child.name):
            shutil.rmtree(child, ignore_errors=True)


def main() -> None:
    clean_previous_outputs()
    plugin_path = resolve_plugin()

    versions = sorted(
        entry.name
        for entry in PROTO_ROOT.iterdir()
        if entry.is_dir() and VERSION_DIR_RE.match(entry.name)
    )
    if not versions:
        raise FileNotFoundError(f"No version directories found under {PROTO_ROOT}")

    for version in versions:
        if version in LEGACY_VERSIONS:
            generate_legacy(version, plugin_path)
        else:
            generate_modern(version, plugin_path)

    write_package_files(versions)
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    print("Done.")


if __name__ == "__main__":
    main()
